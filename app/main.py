from fastapi import FastAPI
from typing import List
from .schemas import *
from .util import discover_candidate_urls, base_from_domain, domain_of, looks_blocklisted, normalize_company_name
from .fetch import fetch_many, discover_feeds_from_html
from .parsers.context import extract_bullets
from .parsers.jobs import parse_job_jsonld, summarize_jobs, usefulness_score
from .parsers.techstack import detect_tech
from bs4 import BeautifulSoup
import httpx

app = FastAPI(title="Maxi GTM Scan", version="0.2.0")

@app.get("/health")
def health():
    return {"ok": True}

def _socials_from_html(html: str) -> dict:
    out = {}
    if not html: return out
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/company" in href:
            out.setdefault("linkedin", href)
        elif "twitter.com" in href or "x.com" in href:
            out.setdefault("twitter", href)
        elif "youtube.com" in href:
            out.setdefault("youtube", href)
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        out.setdefault("site_name", og_site["content"])
    return out

@app.post("/scan", response_model=ScanResponse)
async def scan(req: ScanRequest):
    base = base_from_domain(req.domain)

    # Intenta primero scrapear la home
    from .fetch import extract_internal_links
    from .util import keyword_score, looks_blocklisted, discover_candidate_urls

    home_html = (await fetch_many([base], respect_robots=req.respect_robots, timeout=req.timeout_sec))[0][1]

    candidates = []
    if home_html:
        # 1) saca enlaces internos
        links = extract_internal_links(base, home_html, max_links=300)
        # 2) asigna puntaje por keywords (EN/ES)
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
        # fallback: paths EN/ES por defecto
        candidates = discover_candidate_urls(base)

    # Merge con opcionales
    candidates += [str(u) for u in req.extra_urls] + [str(u) for u in req.careers_overrides]

    # Dedupe y limitar por presupuesto
    seen = set(); clean = []
    for u in candidates:
        if u not in seen and not looks_blocklisted(u):
            seen.add(u); clean.append(u)
    candidates = clean[:req.max_pages]


    # 2) Fetch
    fetched = await fetch_many(candidates, respect_robots=req.respect_robots, timeout=req.timeout_sec)

    pages: List[str] = []
    bullets: List[ContextBullet] = []
    feeds, social, tech, jobs = set(), {}, [], []

    normalized_name = normalize_company_name(req.company_name)

    for final_url, html in fetched:
        if not html: 
            continue
        pages.append(final_url)
        # Context
        bullets.extend(extract_bullets(final_url, html, company_name=normalized_name))
        for f in discover_feeds_from_html(final_url, html):
            feeds.add(f)
        s = _socials_from_html(html)
        for k,v in s.items():
            social.setdefault(k, v)
        # Tech
        tech.extend(detect_tech(final_url, html))
        # Jobs
        jobs.extend(parse_job_jsonld(final_url, html))

    # Si vino linkedin por input, priorizarlo
    if req.company_linkedin:
        social["linkedin"] = str(req.company_linkedin)

    # Dedupe tech
    tech_map = {}
    for t in tech:
        tech_map[(t.category, t.tool)] = t
    tech = list(tech_map.values())

    # Dedupe jobs por (title + apply/source)
    j_seen, j_uniq = set(), []
    for j in jobs:
        k = (j.title.lower(), j.apply_url or j.source_url)
        if j.title and k not in j_seen:
            j_seen.add(k)
            j_uniq.append(j)

    # Resumen + utilidad
    summary = summarize_jobs(j_uniq)
    usef = usefulness_score(j_uniq)

    context_block = ContextBlock(
        bullets=bullets[:60],
        feeds=list(feeds),
        social=social,
        company_name=normalized_name
    )

    return ScanResponse(
        domain=domain_of(base),
        pages_crawled=pages,
        context=context_block,
        tech_stack=tech,
        jobs=JobsBlock(
            postings=j_uniq[:120],
            summary=JobsSignalsSummary(**summary),
            usefulness=JobsUsefulness(**usef)
        )
    )
