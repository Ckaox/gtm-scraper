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
from .parsers.jobs import parse_job_jsonld, summarize_jobs, usefulness_score
from .parsers.techstack import detect_tech
from .parsers.jobs_sources import discover_job_sources


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
        t = getattr(b, "text", None) or (b if isinstance(b, str) else None)
        if not t:
            continue
        s = t.strip()
        if not s:
            continue
        low = s.lower()
        if any(x in low for x in ["cookies", "aviso legal", "privacidad", "privacy", "terms", "condiciones", "copyright"]):
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
    job_sources = []

    # 1) Intentar scrapear la home
    from .fetch import extract_internal_links  # import local para evitar ciclos
    home_html = (await fetch_many([base], respect_robots=req.respect_robots, timeout=req.timeout_sec))[0][1]

    candidates: List[str] = []
    if home_html:
        # 1) links internos
        links = extract_internal_links(base, home_html, max_links=300)
        # 2) puntuar por keywords (EN/ES)
        scored = []
        for u in links:
            if looks_blocklisted(u):
                continue
            scored.append((keyword_score(httpx.URL(u).path), u))
        scored.sort(reverse=True, key=lambda x: x[0])
        # 3) home + top relevantes
        top = [u for _, u in scored]
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
    feeds, social, tech, jobs = set(), {}, [], []

    normalized_name = normalize_company_name(req.company_name)

    # 3) Procesar páginas y descubrir fuentes de empleo
    for final_url, html in fetched:
        if not html:
            continue

        pages.append(final_url)

        # Contexto
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

        # Jobs (JSON-LD locales)
        jobs.extend(parse_job_jsonld(final_url, html))

        # Detectar portales/páginas de careers
        for src_name, jobs_url, fetchable in discover_job_sources(final_url, html):
            try:
                jobs_url_abs = str(httpx.URL(final_url).join(jobs_url))
            except Exception:
                jobs_url_abs = jobs_url

            job_sources.append({"name": src_name, "url": jobs_url_abs, "fetchable": fetchable})

            if fetchable and not looks_blocklisted(jobs_url_abs):
                candidates.append(jobs_url_abs)

    # Si vino linkedin por input, priorizarlo
    if req.company_linkedin:
        social["linkedin"] = str(req.company_linkedin)

    # 4) Re-fetch selectivo de nuevas URLs de empleo (solo delta)
    seen_pages = set(pages)
    new_candidates: List[str] = []
    for u in candidates:
        if u not in seen_pages and not looks_blocklisted(u):
            seen_pages.add(u)
            new_candidates.append(u)

    if new_candidates:
        fetched_jobs = await fetch_many(new_candidates, respect_robots=req.respect_robots, timeout=req.timeout_sec)
        for final_url, html in fetched_jobs:
            if not html:
                continue
            jobs.extend(parse_job_jsonld(final_url, html))

    # 5) Dedupe jobs por (title + apply/source)
    j_seen, j_uniq = set(), []
    for j in jobs:
        k = (j.title.lower(), j.apply_url or j.source_url)
        if j.title and k not in j_seen:
            j_seen.add(k)
            j_uniq.append(j)

    # 6) Resumen + utilidad de ofertas
    summary = summarize_jobs(j_uniq)
    usef = usefulness_score(j_uniq)

    # 7) Agrupar tech por herramienta (evita duplicados y une evidencias)
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

    # 8) Context condensado
    context_block = ContextBlock(
        bullets=[ContextBullet(text=t) for t in condense_bullets(bullets, max_out=10)],
        feeds=list(feeds) if req.include_feeds else [],
        social=social,
        company_name=normalized_name
    )

    # 9) Respuesta final
    return ScanResponse(
        domain=domain_of(base),
        pages_crawled=pages,
        context=context_block,
        tech_stack=tech,
        jobs=JobsBlock(
            postings=j_uniq[:120],
            summary=JobsSignalsSummary(**summary),
            usefulness=JobsUsefulness(**usef)
        ),
        job_sources=[JobSource(**js) for js in job_sources]
    )
