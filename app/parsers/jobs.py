import json, re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..schemas import JobPosting, JobsSignalsSummary
from ..util import looks_blocklisted
from datetime import datetime, timezone
from dateutil import parser as dtp

PLATFORM_HINTS = {
    "greenhouse": ["boards.greenhouse.io", "gh-src"],
    "lever":      ["jobs.lever.co"],
    "workable":   ["apply.workable.com"],
    "smartrecruiters": ["smartrecruiters.com"],
    "breezy":     ["breezy.hr"],
    "ashby":      ["jobs.ashbyhq.com"],
}

def _platform_from_html(html: str) -> str|None:
    h = html.lower()
    for k, hints in PLATFORM_HINTS.items():
        if any(s in h for s in hints):
            return k
    return None

def parse_job_jsonld(url: str, html: str) -> List[JobPosting]:
    out: List[JobPosting] = []
    if not html or looks_blocklisted(url):
        return out
    soup = BeautifulSoup(html, "lxml")

    # JSON-LD
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and (it.get("@type") == "JobPosting" or "JobPosting" in str(it.get("@type"))):
                title = (it.get("title") or "").strip()
                if not title:
                    continue
                loc = None
                locData = it.get("jobLocation")
                if isinstance(locData, dict):
                    loc = (locData.get("address",{}) or {}).get("addressLocality")
                if isinstance(locData, list) and locData and isinstance(locData[0], dict):
                    loc = (locData[0].get("address",{}) or {}).get("addressLocality")
                out.append(JobPosting(
                    title=title,
                    location=loc,
                    employment_type=(it.get("employmentType") or None),
                    department=(it.get("hiringOrganization",{}) or {}).get("department"),
                    date_posted=it.get("datePosted"),
                    valid_through=it.get("validThrough"),
                    apply_url=(it.get("hiringOrganization",{}) or {}).get("sameAs") or url,
                    platform_hint=_platform_from_html(html),
                    source_url=url
                ))

    # Fallback: regex títulos
    if not out:
        titles = []
        for tag in soup.select("a, h2, h3, li"):
            txt = " ".join(tag.get_text(" ").split())
            if 5 <= len(txt) <= 120 and re.search(r"(engineer|developer|marketing|sales|account|designer|data|product|success|support|finance|hr|talent|recruit)", txt, re.I):
                titles.append(txt)
        titles = list(dict.fromkeys(titles))[:20]
        out = [JobPosting(title=t, source_url=url) for t in titles]

    return out

def guess_function(title: str) -> str:
    t = title.lower()
    mapping = {
        "sales": "Sales", "account executive": "Sales", "sdr": "Sales", "bdr": "Sales",
        "revops": "RevOps", "revenue operations": "RevOps",
        "marketing": "Marketing", "growth": "Marketing", "demand": "Marketing",
        "data": "Data", "analytics": "Data", "machine learning": "Data",
        "engineer": "Engineering", "developer": "Engineering",
        "product": "Product", "pm": "Product",
        "design": "Design",
        "customer success": "CS", "support": "CS",
        "finance": "Finance", "hr": "People", "talent": "People", "recruit": "People"
    }
    for k, v in mapping.items():
        if k in t:
            return v
    return "Other"

def guess_seniority(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["head", "vp", "vice president", "director", "lead"]):
        return "Lead/Director+"
    if any(w in t for w in ["senior", "sr.", "staff", "principal"]):
        return "Senior"
    if any(w in t for w in ["junior", "jr.", "associate", "intern"]):
        return "Junior"
    if "manager" in t:
        return "Manager"
    return "Mid"

def summarize_jobs(jobs: List[JobPosting]) -> Dict[str, Any]:
    functions: Dict[str, int] = {}
    seniority: Dict[str, int] = {}
    for j in jobs:
        f = guess_function(j.title)
        functions[f] = functions.get(f, 0) + 1
        s = guess_seniority(j.title)
        seniority[s] = seniority.get(s, 0) + 1
    focus = sorted(functions.items(), key=lambda x: x[1], reverse=True)[:3]
    return {
        "hiring_focus": [k for k,_ in focus],
        "seniority_mix": seniority,
        "functions_count": functions
    }

def _days_from_now(dt_str: str|None) -> int|None:
    if not dt_str: return None
    try:
        d = dtp.parse(dt_str)
        if not d.tzinfo: d = d.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - d).days))
    except Exception:
        return None

def usefulness_score(jobs: List[JobPosting]) -> Dict[str, Any]:
    if not jobs:
        return {"score":0.0, "tags":[], "reasons":[], "freshness_days_p50": None, "velocity":{"jobs_count":0,"platforms":{}}}

    summ = summarize_jobs(jobs)
    functions = summ["functions_count"]
    seniority = summ["seniority_mix"]

    score = 0.0
    tags, reasons = [], []

    # leadership
    leaders = sum(v for k,v in seniority.items() if k in ["Lead/Director+","Manager"])
    if leaders >= 1:
        score += 0.20; tags.append("Leadership hire"); reasons.append("Al menos un rol de liderazgo abierto")

    # frescura
    days = [_days_from_now(j.date_posted) for j in jobs if j.date_posted]
    days = [d for d in days if d is not None]
    p50 = sorted(days)[len(days)//2] if days else None
    if p50 is not None:
        if p50 <= 30: score += 0.20; tags.append("Recent postings")
        elif p50 <= 60: score += 0.10; tags.append("Relatively recent")

    # volumen
    n = len(jobs)
    if 1 <= n <= 3: score += 0.05
    elif 4 <= n <= 10: score += 0.10
    elif n > 10: score += 0.15

    # foco GTM
    gtm = sum(functions.get(k,0) for k in ["Sales","Marketing","CS","RevOps"])
    if gtm >= 2:
        score += 0.15; tags.append("Go-to-market expansion"); reasons.append("Múltiples roles GTM (Sales/Marketing/CS/RevOps)")

    # plataformas
    plats = {}
    for j in jobs:
        if j.platform_hint:
            plats[j.platform_hint] = plats.get(j.platform_hint, 0) + 1
    if plats: score += 0.05

    score = round(min(1.0, score), 2)
    return {"score":score, "tags":list(dict.fromkeys(tags)), "reasons":list(dict.fromkeys(reasons)),
            "freshness_days_p50": p50, "velocity":{"jobs_count": n, "platforms": plats}}
