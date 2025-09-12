import httpx, asyncio
from typing import Tuple, List, Dict
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
import os

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MaxiGTM/0.1; +https://example.com/bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# cache simple de robots por host
_robot_cache: Dict[str, robotparser.RobotFileParser] = {}

# --- Fallback HTTP/2 ---
HTTP2 = os.getenv("HTTP2", "1") == "1"  # default: ON
try:
    import h2  # noqa: F401
except ImportError:
    HTTP2 = False
# ------------------------

def _robots_for(url: str) -> robotparser.RobotFileParser:
    host = urlparse(url).netloc
    if host in _robot_cache:
        return _robot_cache[host]
    rp = robotparser.RobotFileParser()
    rp.set_url(f"https://{host}/robots.txt")
    try:
        rp.read()
    except Exception:
        pass
    _robot_cache[host] = rp
    return rp

async def fetch_many(urls: List[str], respect_robots: bool=True, timeout=10.0):
    async with httpx.AsyncClient(
        http2=HTTP2, headers=DEFAULT_HEADERS, follow_redirects=True
    ) as client:
        tasks = [fetch_html(client, u, respect_robots=respect_robots, timeout=timeout) for u in urls]
        return await asyncio.gather(*tasks)

def discover_feeds_from_html(base_url: str, html: str):
    feeds = set()
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("link", attrs={"type": ["application/rss+xml","application/atom+xml"]}):
        href = link.get("href")
        if href:
            feeds.add(httpx.URL(base_url).join(href).human_repr())
    return list(feeds)

from urllib.parse import urlparse, urljoin

def extract_internal_links(base_url: str, html: str, max_links: int = 200) -> list[str]:
    """Devuelve enlaces internos únicos (mismo dominio) encontrados en la página."""
    if not html:
        return []
    base = httpx.URL(base_url)
    host = base.host
    soup = BeautifulSoup(html, "lxml")
    out = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        try:
            absu = httpx.URL(base).join(href).human_repr()
        except Exception:
            continue
        u = httpx.URL(absu)
        # mismo dominio o subdominio
        if u.host and host and u.host.endswith(host.split(".", 1)[-1]):  # permite subdominios
            if absu not in seen:
                seen.add(absu); out.append(absu)
        if len(out) >= max_links:
            break
    return out