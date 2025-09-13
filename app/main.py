# app/app/main.py
from fastapi import FastAPI
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import httpx
import time

from .schemas import *
from .util import (
    discover_candidate_urls,
    base_from_domain,
    domain_of,
    looks_blocklisted,
    normalize_company_name,
    keyword_score,
)
from .fetch import fetch_many, discover_feeds_from_html
from .parsers.context import extract_bullets
from .parsers.techstack import detect_tech
from .parsers.news import extract_news_from_html
from .parsers.emails import extract_emails
from .parsers.industry import detectar_principal_y_secundaria, detectar_industrias
from .parsers.company_name import extract_company_name_from_html
from .parsers.linkedin import extract_linkedin_url_from_html, get_company_size_segment, analyze_company_maturity_simple
from .parsers.growth_signals import detect_growth_signals, calculate_growth_score
from .parsers.seo_metrics import extract_seo_metrics
from .parsers.competitors import detect_competitors_from_content


# ===========================
# Config rápida (tuning perf)
# ===========================
MAX_INTERNAL_LINKS = 100          # Reducido para Render: 150→100
TOP_CANDIDATES_BY_KEYWORD = 15    # Reducido: 20→15
MAX_PAGES_FREE_PLAN = 6           # Límite para plan free de Render


# ---------------------------
# Utilidades locales
# ---------------------------

def condense_bullets(raw_bullets: List["ContextBullet"], max_out: int = 8) -> List[str]:
    """
    Selecciona hasta max_out frases útiles priorizando contenido con keywords de negocio.
    Deduplica y evita secciones legales o repetitivas.
    """
    texts = []
    for b in raw_bullets:
        # Acepta ContextBullet(bullet=...) o ContextBullet(text=...)
        t = (
            getattr(b, "text", None)
            or getattr(b, "bullet", None)
            or (b if isinstance(b, str) else None)
        )
        if not t:
            continue
        s = t.strip()
        if not s:
            continue
        low = s.lower()
        # filtra ruido legal/común
        if any(x in low for x in [
            "cookies", "aviso legal", "privacidad", "privacy",
            "terms", "condiciones", "copyright"
        ]):
            continue
        texts.append(s)

    PRIORITY = [
        "servicio", "servicios", "producto", "productos", "solución", "soluciones",
        "clientes", "casos de éxito", "sectores", "integración", "api",
        "demo", "contacto", "reserv", "precios", "pricing",
        "empleo", "careers", "trabaja", "equipo", "fundado", "oficinas"
    ]

    scored = []
    for s in texts:
        score = sum(1 for k in PRIORITY if k in s.lower())
        ln = len(s)
        if 60 <= ln <= 240:
            score += 1
        scored.append((score, s))

    scored.sort(reverse=True, key=lambda x: x[0])

    out, seen = [], set()
    for _, s in scored:
        key = " ".join(s.lower().split())
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_out:
            break
    return out


def _socials_from_html(html: str) -> dict:
    """Extract social networks from HTML"""
    out = {}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")

    # 1) Enlaces visibles
    for a in soup.find_all("a", href=True):
        href = a["href"]
        h = href.lower()
        if "linkedin.com/company" in h or "linkedin.com/in/" in h:
            out.setdefault("linkedin", href)
        elif "twitter.com" in h or "x.com/" in h:
            out.setdefault("twitter", href)
        elif "youtube.com" in h or "youtu.be" in h:
            out.setdefault("youtube", href)
        elif "instagram.com" in h:
            out.setdefault("instagram", href)
        elif "facebook.com" in h:
            out.setdefault("facebook", href)
        elif "tiktok.com" in h:
            out.setdefault("tiktok", href)
        elif "github.com" in h:
            out.setdefault("github", href)

    # 2) JSON-LD Organization sameAs
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "{}")
            items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ["Organization", "LocalBusiness", "Corporation"]:
                    same = item.get("sameAs") or []
                    if isinstance(same, str):
                        same = [same]
                    for href in same:
                        h = href.lower()
                        if "linkedin.com" in h: out.setdefault("linkedin", href)
                        elif "twitter.com" in h or "x.com/" in h: out.setdefault("twitter", href)
                        elif "youtube.com" in h or "youtu.be" in h: out.setdefault("youtube", href)
                        elif "instagram.com" in h: out.setdefault("instagram", href)
                        elif "facebook.com" in h: out.setdefault("facebook", href)
                        elif "tiktok.com" in h: out.setdefault("tiktok", href)
                        elif "github.com" in h: out.setdefault("github", href)
        except Exception:
            pass

    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        out.setdefault("site_name", og_site["content"])
    return out


# ---------------------------
# FastAPI
# ---------------------------

app = FastAPI(title="Maxi GTM Scan", version="0.2.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/scan", response_model=ScanResponse)
async def scan(req: ScanRequest):
    base = base_from_domain(req.domain)

    # 1) Intentar scrapear la home
    from .fetch import extract_internal_links  # import local para evitar ciclos
    start_time = time.time()
    home_html = (await fetch_many([base], respect_robots=req.respect_robots, timeout=req.timeout_sec))[0][1]
    home_load_time = int((time.time() - start_time) * 1000)

    candidates: List[str] = []
    if home_html:
        # 1) links internos (reducido por perf)
        links = extract_internal_links(base, home_html, max_links=MAX_INTERNAL_LINKS)
        # 2) puntuar por keywords (EN/ES)
        scored = []
        for u in links:
            if looks_blocklisted(u):
                continue
            scored.append((keyword_score(httpx.URL(u).path), u))
        scored.sort(reverse=True, key=lambda x: x[0])
        # 3) home + top relevantes (recortado por perf)
        top = [u for _, u in scored[:TOP_CANDIDATES_BY_KEYWORD]]
        candidates = [base] + top
    else:
        # Fallback: paths EN/ES por defecto
        candidates = discover_candidate_urls(base)

    # Merge con opcionales
    candidates += [str(u) for u in req.extra_urls] + [str(u) for u in req.careers_overrides]

    # Dedupe y presupuesto (ajustado para Render free plan)
    seen = set(); clean = []
    for u in candidates:
        if u not in seen and not looks_blocklisted(u):
            seen.add(u); clean.append(u)
    
    # Límite más agresivo para plan free
    max_pages = min(req.max_pages, MAX_PAGES_FREE_PLAN)
    candidates = clean[:max_pages]

    # 2) Fetch inicial
    fetched = await fetch_many(candidates, respect_robots=req.respect_robots, timeout=req.timeout_sec)

    pages: List[str] = []
    bullets: List[ContextBullet] = []
    social = {}
    tech = []
    news_items: List[NewsItem] = []
    emails: List[str] = []
    contact_pages: List[str] = []
    
    # Competitor detection variables
    competitors_found = set()

    normalized_name = normalize_company_name(req.company_name) if req.company_name else None

    # 3) Procesar páginas
    for final_url, html in fetched:
        if not html:
            continue

        pages.append(final_url)

        # Contexto (bullets brutos) - reducido
        bullets.extend(extract_bullets(final_url, html, company_name=normalized_name))

        # Social networks extraction
        s = _socials_from_html(html)
        for k, v in s.items():
            social.setdefault(k, v)

        # Tech detection (ahora agrupado por categoría)
        tech.extend(detect_tech(final_url, html))

        # Emails (will be moved to social)
        page_emails = extract_emails(html)
        emails.extend(page_emails)

        # Contact pages detection
        if any(contact_word in final_url.lower() for contact_word in ["contact", "contacto", "about", "empresa"]):
            contact_pages.append(final_url)

        # Competitor detection
        detected_competitors = detect_competitors_from_content(html, None)  # We'll fix this
        competitors_found.update(detected_competitors)

        # Noticias internas: limitadas a 3 más recientes
        path_lower = httpx.URL(final_url).path.lower()
        looks_news = any(k in path_lower for k in ("blog", "news", "press", "novedad", "prensa"))
        if looks_news or BeautifulSoup(html, "lxml").find("article"):
            page_news = extract_news_from_html(final_url, html, max_items=2)  # Reducido a 2 por página
            news_items.extend(page_news)

    # 4) Company name extraction con múltiples métodos
    company_name = extract_company_name_from_html(
        home_html if home_html else "", 
        req.domain, 
        fallback_name=normalized_name
    )

    # 5) Agrupar tech por categoría (nueva estructura)
    tech_by_category = {}
    for t in tech:
        category = getattr(t, "category", "Other")
        tools = getattr(t, "tools", [])
        evidence = getattr(t, "evidence", "")
        
        if category not in tech_by_category:
            tech_by_category[category] = {
                "tools": set(),
                "evidence": []
            }
        
        if isinstance(tools, list):
            tech_by_category[category]["tools"].update(tools)
        else:
            tech_by_category[category]["tools"].add(tools)
        
        if evidence:
            tech_by_category[category]["evidence"].append(evidence)

    tech_stack = [
        TechFingerprint(
            category=cat,
            tools=list(data["tools"]),
            evidence=" | ".join(data["evidence"][:2])  # Limit evidence
        )
        for cat, data in tech_by_category.items()
    ]

    # 6) Context condensado (sin feeds)
    context_block = ContextBlock(
        bullets=[ContextBullet(text=t) for t in condense_bullets(bullets, max_out=8)]
    )

    # 7) Detectar industria del texto consolidado
    texto_completo = " ".join([b.bullet for b in context_block.bullets]) + " " + " ".join(pages)
    principal, secundaria = detectar_principal_y_secundaria(texto_completo)

    # 8) SEO metrics (mejoradas con tiempo de carga)
    seo_metrics = {}
    if home_html:
        seo_metrics = extract_seo_metrics(home_html, base, request_time_ms=home_load_time)

    # 9) Integrar emails en social
    if emails:
        # Deduplicate emails
        unique_emails = list(set(emails))
        social["emails"] = unique_emails[:5]  # Limit to 5 emails

    # 10) Limitar noticias a las 3 más recientes
    recent_news = news_items[:3] if news_items else []

    # 11) Respuesta final reorganizada
    response_data = {
        "domain": domain_of(base),
        "company_name": company_name,
        "context": context_block,
        "social": social,
        "industry": principal,
        "industry_secondary": secundaria,
        "tech_stack": tech_stack,
        "competitors": list(competitors_found),
        "seo_metrics": seo_metrics if seo_metrics else None,
        "pages_crawled": pages,
        "recent_news": [NewsItem(title=item["title"], body=item["body"], url=item["url"]) for item in recent_news],
        "contact_pages": contact_pages,
    }

    # Only include fields that have meaningful data
    filtered_response = {}
    for key, value in response_data.items():
        if value is not None and value != [] and value != {}:
            filtered_response[key] = value
        elif key in ["domain", "company_name", "context"]:  # Always include these core fields
            filtered_response[key] = value

    return ScanResponse(**filtered_response)


