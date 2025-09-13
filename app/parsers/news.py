# app/app/parsers/news.py
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import httpx

def _text(n):
    return " ".join((n.get_text(" ", strip=True) or "").split())

CANDIDATE_PATHS = re.compile(r"/(blog|news|novedades|press|prensa)/", re.I)

def extract_news_from_html(base_url: str, html: str, max_items: int = 5) -> List[Dict[str, str]]:
    """
    Extrae hasta max_items noticias internas (title + body + url) de una página que
    parezca ser blog/news/press o que tenga <article>.
    """
    out = []
    if not html:
        return out

    soup = BeautifulSoup(html, "lxml")

    # 1) Prioriza <article> con <h1>/<h2> y párrafos
    articles = soup.find_all("article")
    for art in articles:
        h = art.find(["h1", "h2", "h3"])
        if not h: 
            continue
        title = _text(h)
        if not title:
            continue
        # cuerpo = unión de párrafos razonables
        ps = [p for p in art.find_all("p")][:6]
        body = _text(ps[0]) if ps else ""
        if not body:
            # fallback: siguiente sibling
            sib = h.find_next("p")
            body = _text(sib) if sib else ""
        # url
        a = h.find("a", href=True) or art.find("a", href=True)
        if a and a["href"]:
            url = str(httpx.URL(base_url).join(a["href"]))
        else:
            url = base_url

        if title and body:
            out.append({"title": title, "body": body, "url": url})
        if len(out) >= max_items:
            return out

    # 2) Si no hubo <article>, intenta tarjetas típicas de blog (h2/h3 + p + a)
    if not out:
        cards = soup.select("section a, div a")
        seen = set()
        for a in cards:
            href = a.get("href")
            if not href or href in seen:
                continue
            seen.add(href)
            # buscar heading cercano
            h = a.find(["h1", "h2", "h3"]) or a.find_parent().find(["h1", "h2", "h3"]) if a.find_parent() else None
            if not h:
                continue
            title = _text(h)
            if not title:
                continue
            # párrafo cercano
            p = a.find("p") or (a.find_parent().find("p") if a.find_parent() else None)
            body = _text(p) if p else ""
            url = str(httpx.URL(base_url).join(href))
            if title and body:
                out.append({"title": title, "body": body, "url": url})
            if len(out) >= max_items:
                break

    return out[:max_items]
