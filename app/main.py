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
    smart_domain_resolver,
    domain_of,
    looks_blocklisted,
    normalize_company_name,
    keyword_score,
)
from .fetch import fetch_many
from .parsers.techstack import detect_tech
from .parsers.news import extract_news_from_html
from .parsers.emails import extract_emails
from .parsers.industry import detectar_principal_y_secundaria
from .parsers.company_name import extract_company_name_from_html
from .parsers.seo_metrics import extract_seo_metrics


# ===========================
# Config rápida (tuning perf) - FINAL OPTIMIZATION
# ===========================
MAX_INTERNAL_LINKS = 60           # Reducido aún más: 80→60
TOP_CANDIDATES_BY_KEYWORD = 8     # Reducido aún más: 10→8  
MAX_PAGES_FREE_PLAN = 3           # Reducido aún más: 4→3


# ---------------------------
# Utilidades locales
# ---------------------------

def _socials_from_html(html: str) -> dict:
    """Extract social networks from HTML - improved to avoid wrong URLs"""
    out = {}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")

    # Find social links with improved filtering
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"].strip()
        if not href:
            continue
        
        href_lower = href.lower()
        
        # Skip obvious non-social pages - enhanced filtering
        if any(skip in href_lower for skip in [
            "privacy", "privacidad", "terms", "condiciones", 
            "cookies", "legal", "contact", "contacto", "notices",
            "policy", "politica", "about/legal", "support", 
            "help", "ayuda", "faq", "aviso", "disclaimer"
        ]):
            continue
            
        # Skip obviously wrong URLs (too long, weird parameters)
        if len(href) > 200 or "?" in href and len(href.split("?")[1]) > 50:
            continue
        
        # Detect social networks with better filtering
        if "linkedin.com/company" in href_lower and "linkedin" not in out:
            out["linkedin"] = href
        elif "facebook.com" in href_lower and "facebook" not in out:
            # Only valid Facebook pages
            if "/pages/" in href_lower or (href_lower.count("/") >= 3 and not any(x in href_lower for x in ["sharer", "login", "help"])):
                out["facebook"] = href
        elif ("twitter.com" in href_lower or "x.com" in href_lower) and "twitter" not in out:
            # Skip Twitter share/login links
            if not any(x in href_lower for x in ["share", "login", "oauth", "auth"]):
                out["twitter"] = href
        elif "instagram.com" in href_lower and "instagram" not in out:
            if not any(x in href_lower for x in ["share", "login", "oauth"]):
                out["instagram"] = href
        elif "youtube.com" in href_lower and "youtube" not in out:
            if any(x in href_lower for x in ["/channel/", "/c/", "/user/", "/@"]):
                out["youtube"] = href
        elif "tiktok.com" in href_lower and "tiktok" not in out:
            if not any(x in href_lower for x in ["share", "login"]):
                out["tiktok"] = href
        elif "github.com" in href_lower and "github" not in out:
            if not any(x in href_lower for x in ["login", "signup"]):
                out["github"] = href

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
    # 🎯 SMART DOMAIN RESOLUTION - Resuelve automáticamente www/non-www
    print(f"🔍 Resolviendo dominio inteligentemente: {req.domain}")
    base = smart_domain_resolver(req.domain, timeout=req.timeout_sec)
    print(f"✅ Dominio resuelto a: {base}")

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
    social = {}
    tech = []
    news_items: List[NewsItem] = []
    emails: List[str] = []

    normalized_name = normalize_company_name(req.company_name) if req.company_name else None

    # 3) Procesar páginas - optimized for speed
    for final_url, html in fetched:
        if not html:
            continue

        pages.append(final_url)

        # Social networks extraction (simplified)
        if len(social) < 3:  # Limit social processing
            s = _socials_from_html(html)
            for k, v in s.items():
                if k not in social:  # Avoid duplicates
                    social[k] = v

        # Tech detection (optimized)
        tech.extend(detect_tech(final_url, html))

        # Emails (optimized - only from first 2 pages)
        if len(pages) <= 2:
            page_emails = extract_emails(html)
            emails.extend(page_emails[:3])  # Max 3 emails per page

        # News detection - very limited for performance
        if len(news_items) == 0:  # Only process news from first page that has it
            path_lower = httpx.URL(final_url).path.lower()
            if any(k in path_lower for k in ("blog", "news")):
                page_news = extract_news_from_html(final_url, html, max_items=1)
                news_items.extend(page_news)

    # 4) Company name extraction con múltiples métodos
    company_name = extract_company_name_from_html(
        home_html if home_html else "", 
        req.domain, 
        fallback_name=normalized_name
    )

        # 5) Tech stack restructured as dict by category (new format)
    tech_by_category = {}
    for tech_item in tech:
        # tech_item is now a dict from detect_tech
        category = tech_item.get("category", "other")
        if category not in tech_by_category:
            tech_by_category[category] = {"tools": set(), "evidence": []}
        
        # tech_item["tools"] is already a list
        tech_by_category[category]["tools"].update(tech_item.get("tools", []))
        
        evidence = tech_item.get("evidence", "")
        if evidence:
            tech_by_category[category]["evidence"].append(evidence)

    # Create tech_stack as dict
    tech_stack = {}
    for cat, data in tech_by_category.items():
        tech_stack[cat] = TechFingerprint(
            tools=list(data["tools"]),
            evidence=" | ".join(data["evidence"][:2])  # Limit evidence
        )

    # 6) Context block simplified - no bullets for performance
    context_block = ContextBlock()

    # 7) Detectar industria from pages content (optimized)
    # Use only first page and company name for faster processing
    texto_completo = pages[0] if pages else ""
    if company_name:
        texto_completo += " " + company_name
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

    # 11) Respuesta final reorganizada (nueva estructura sin competitors ni contact_pages)
    response_data = {
        "domain": domain_of(base),
        "company_name": company_name,
        "context": context_block,
        "social": social,
        "industry": principal,
        "industry_secondary": secundaria,
        "tech_stack": tech_stack,
        "seo_metrics": seo_metrics if seo_metrics else None,
        "pages_crawled": pages,
        "recent_news": [NewsItem(title=item["title"], body=item["body"], url=item["url"]) for item in recent_news],
    }

    # Only include fields that have meaningful data
    filtered_response = {}
    for key, value in response_data.items():
        if value is not None and value != [] and value != {}:
            filtered_response[key] = value
        elif key in ["domain", "company_name", "context"]:  # Always include these core fields
            filtered_response[key] = value

    return ScanResponse(**filtered_response)


