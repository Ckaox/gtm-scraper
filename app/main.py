# app/app/main.py
from fastapi import FastAPI
from typing import List
from bs4 import BeautifulSoup
import httpx

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
from .parsers.industry import detect_industry
from .parsers.industry import detectar_industrias, detectar_principal_y_secundaria


# ===========================
# Config rápida (tuning perf)
# ===========================
MAX_INTERNAL_LINKS = 150          # antes 300
TOP_CANDIDATES_BY_KEYWORD = 20    # cortar top-K por score


# ---------------------------
# Utilidades locales
# ---------------------------

def condense_bullets(raw_bullets: List["ContextBullet"], max_out: int = 10) -> List[str]:
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
    home_html = (await fetch_many([base], respect_robots=req.respect_robots, timeout=req.timeout_sec))[0][1]

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

    # Dedupe y presupuesto
    seen = set(); clean = []
    for u in candidates:
        if u not in seen and not looks_blocklisted(u):
            seen.add(u); clean.append(u)
    candidates = clean[:req.max_pages]

    # 2) Fetch inicial
    fetched = await fetch_many(candidates, respect_robots=req.respect_robots, timeout=req.timeout_sec)

    pages: List[str] = []
    bullets: List[ContextBullet] = []
    feeds, social, tech = set(), {}, []
    news_items: List[NewsItem] = []

    normalized_name = normalize_company_name(req.company_name)

    # 3) Procesar páginas
    for final_url, html in fetched:
        if not html:
            continue

        pages.append(final_url)

        # Contexto (bullets brutos)
        bullets.extend(extract_bullets(final_url, html, company_name=normalized_name))

        # Feeds (solo si lo pide el request)
        if req.include_feeds:
            for f in discover_feeds_from_html(final_url, html):
                feeds.add(f)

        # Social
        s = _socials_from_html(html)
        for k, v in s.items():
            social.setdefault(k, v)

        # Tech
        tech.extend(detect_tech(final_url, html))

        # Noticias internas: si la URL parece blog/news/press, o si hay <article>
        path_lower = httpx.URL(final_url).path.lower()
        looks_news = any(k in path_lower for k in ("blog", "news", "press", "novedad", "prensa"))
        if looks_news or BeautifulSoup(html, "lxml").find("article"):
            news_items.extend(extract_news_from_html(final_url, html, max_items=5))

    # 4) Agrupar tech por herramienta (evita duplicados y une evidencias)
    tech_by_tool = {}
    for t in tech:
        key = getattr(t, "tool", None) or getattr(t, "Tool", None) or "Desconocido"
        cat = getattr(t, "category", None) or getattr(t, "Category", None) or "Otros"
        ev  = getattr(t, "evidence", None) or getattr(t, "Evidence", None) or ""
        entry = tech_by_tool.setdefault(key, {"tool": key, "category": cat, "ev": set()})
        if ev:
            entry["ev"].add(ev)

    tech = [
        TechFingerprint(tool=v["tool"], category=v["category"], evidence=" | ".join(sorted(v["ev"])))
        for v in tech_by_tool.values()
    ]

    # 5) Context condensado
    context_block = ContextBlock(
        bullets=[ContextBullet(text=t) for t in condense_bullets(bullets, max_out=10)],
        feeds=list(feeds) if req.include_feeds else [],
        social=social,
        company_name=normalized_name
    )

    # 6) Respuesta final 
    return ScanResponse(
        domain=domain_of(base),
        pages_crawled=pages,
        context=context_block,
        tech_stack=tech,
        industry=principal,
        industry_secondary=secundaria,
        industry_evidence=evidencias
    )
        

