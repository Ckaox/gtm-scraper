import httpx, asyncio
from urllib.parse import urlparse
from typing import Tuple, List, Dict
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MaxiGTM/0.1; +https://example.com/bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# cache simple de robots por host
_robot_cache: Dict[str, robotparser.RobotFileParser] = {}

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

async def fetch_html(client: httpx.AsyncClient, url: str, respect_robots: bool=True, timeout=10.0) -> Tuple[str, str]:
    try:
        if respect_robots:
            rp = _robots_for(url)
            if hasattr(rp, "can_fetch") and not rp.can_fetch(DEFAULT_HEADERS["User-Agent"], url):
                return url, ""  # bloqueado por robots

        r = await client.get(url, timeout=timeout)
        r.raise_for_status()
        ct = r.headers.get("content-type","")
        if "text/html" not in ct and "application/xhtml" not in ct:
            return str(r.url), ""
        return str(r.url), r.text
    except Exception:
        return url, ""

async def fetch_many(urls: List[str], respect_robots: bool=True, timeout=10.0):
    async with httpx.AsyncClient(http2=True, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
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
