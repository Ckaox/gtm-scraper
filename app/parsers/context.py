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
    
    # Limitar HTML para performance
    if len(html) > 500_000:  # 500KB max
        html = html[:500_000]
    
    soup = BeautifulSoup(html, "lxml")

    t = soup.title.string.strip() if soup.title and soup.title.string else None
    if t and not any(bad in t.lower() for bad in BOILERPLATE):
        out.append(ContextBullet(source_url=url, bullet=t, kind="generic"))

    md = soup.find("meta", attrs={"name":"description"})
    if md and md.get("content"):
        txt = md["content"].strip()
        if txt and not any(b in txt.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=txt, kind="generic"))

    # Reducir la búsqueda de headings para performance
    for tag in soup.find_all(HEADINGS)[:15]:  # Máximo 15 headings
        text = " ".join(tag.get_text(" ").split())
        if 6 <= len(text) <= 180 and not any(b in text.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=text, kind=_guess_kind(url)))

    # Reducir la búsqueda de list items para performance
    for li in soup.select("section li, .features li, .benefits li, ul li")[:20]:  # Máximo 20 items
        text = " ".join(li.get_text(" ").split())
        if 6 <= len(text) <= 160 and not any(b in text.lower() for b in BOILERPLATE):
            out.append(ContextBullet(source_url=url, bullet=text, kind=_guess_kind(url)))
        if len(out) >= 20:  # Break early si ya tenemos suficientes
            break

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

    return uniq[:15]  # Reducido de 25 a 15
