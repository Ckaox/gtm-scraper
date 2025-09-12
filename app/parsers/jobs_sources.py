# app/app/parsers/jobs_sources.py
import re
from typing import List, Tuple
from bs4 import BeautifulSoup

# (name, regex, fetchable)
JOB_PORTALS: List[Tuple[str, str, bool]] = [
    # Portales scrapeables con alta probabilidad
    ("Greenhouse", r"boards\.greenhouse\.io/[^/\s]+", True),
    ("Lever", r"jobs\.lever\.co/[^/\s]+", True),
    ("Workable", r"apply\.workable\.com/[^/\s]+", True),
    ("Personio", r"jobs\.personio\.com/[^/\s]+", True),
    ("Ashby", r"jobs\.ashbyhq\.com/[^/\s]+", True),
    ("BambooHR", r"[^/]+\.bamboohr\.com/careers", True),
    ("Recruitee", r"[^/]+\.recruitee\.com", True),
    ("Teamtailor", r"[^/]+\.teamtailor\.com", True),
    ("SmartRecruiters", r"smartrecruiters\.com/[^/\s]+", True),
    ("Workday", r"myworkdayjobs\.com", True),
    ("Breezy", r"breezy\.hr", True),
    ("Taleo", r"taleo\.net/careersection", True),

    # Agregadores o sitios con login/antibot fuerte (no scrapear)
    ("LinkedIn Jobs", r"linkedin\.com/(company|school)/[^/\s]+/jobs/?", False),
    ("LinkedIn Search", r"linkedin\.com/jobs/search", False),
    ("Glassdoor", r"glassdoor\.[a-z.]+/Job", False),
    ("Indeed", r"indeed\.[a-z.]+/.*jobs", False),
    ("Talent.com", r"talent\.com/.*jobs", False),

    # ES / LATAM
    ("InfoJobs", r"infojobs\.(net|es)", True),         # a veces scrap sencillo
    ("Computrabajo", r"computrabajo\.[a-z.]+/ofertas-de-trabajo", True),
    ("Jobandtalent", r"jobandtalent\.com", False),     # suele estar protegido
]

CAREERS_HINTS = [
    "/careers", "/jobs", "/empleo", "/empleos", "/trabaja", "/join-us",
    "/work-with-us", "/carreiras", "/kariera", "/vacancies", "/vacantes"
]

def discover_job_sources(final_url: str, html: str) -> List[Tuple[str, str, bool]]:
    """
    Devuelve [(source_name, url_detectada, fetchable)]
    - fetchable=False => devuélvela al usuario como fuente, pero no intentes scrapearla.
    """
    out: List[Tuple[str, str, bool]] = []
    if not html:
        return out

    soup = BeautifulSoup(html, "lxml")

    # 1) Enlaces a portales externos
    for a in soup.find_all("a", href=True):
        href = a["href"]
        for name, pat, fetchable in JOB_PORTALS:
            if re.search(pat, href, re.I):
                out.append((name, href, fetchable))
                break

    # 2) Paths internos típicos de "Careers"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(h in href.lower() for h in CAREERS_HINTS):
            out.append(("SiteCareers", href, True))

    # Dedupe manteniendo primer fetchable
    seen = set(); uniq: List[Tuple[str, str, bool]] = []
    for name, u, f in out:
        k = (name, u)
        if k not in seen:
            seen.add(k); uniq.append((name, u, f))
    return uniq
