from bs4 import BeautifulSoup
from typing import List, Optional
from ..schemas import ContextBullet
from ..util import looks_blocklisted

HEADINGS = ("h1","h2","h3")

BOILERPLATE = (
    "cookies", "privacy", "terms", "subscribe", "newsletter", "404", "copyright"
)

def _guess_kind(url: str) -> str:
    u = url.lower()
    if "/about" in u or "/company" in u: return "about"
    if "/product" in u or "/platform" in u or "/solutions" in u: return "product"
    if "/blog" in u: return "blog"
    if "/news" in u or "/press" in u: return "news"
    return "value_prop"

def extract_bullets(url: str, html: str, company_name: Optional[str]=None) -> List[ContextBullet]:
    out: List[ContextBullet] = []
    if not html or looks_blocklisted(url):
        return out
    soup = BeautifulSoup(html, "lxml")

    t = soup.title.string.strip() if soup.title and soup.title.string else None
    if t and not any(bad in t.lower() for bad in BOILERPLATE):
        out.append(ContextBullet(source_url=url, bullet=t, kind="generic"))

    md = soup.find("meta", attrs={"name":"description"})
    if md and md.get("content"):
        txt = md["content"].strip()
        if txt and not any(b in txt.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=txt, kind="generic"))

    for tag in soup.find_all(HEADINGS):
        text = " ".join(tag.get_text(" ").split())
        if 6 <= len(text) <= 180 and not any(b in text.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=text, kind=_guess_kind(url)))

    for li in soup.select("section li, .features li, .benefits li, ul li"):
        text = " ".join(li.get_text(" ").split())
        if 6 <= len(text) <= 160 and not any(b in text.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=text, kind=_guess_kind(url)))

    # dedupe y prioriza si menciona company_name
    seen = set()
    uniq = []
    for b in out:
        key = (b.kind, b.bullet.lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(b)

    if company_name:
        cname = company_name.lower()
        uniq.sort(key=lambda x: (cname in x.bullet.lower(), x.kind=="value_prop"), reverse=True)

    return uniq[:25]
