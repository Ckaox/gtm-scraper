# app/app/fetch.py
import os
import asyncio
from typing import Tuple, List, Dict, Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MaxiGTM/0.1; +https://example.com/bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# === Performance knobs ===
HTTP2 = os.getenv("HTTP2", "1") == "1"
MAX_HTML_BYTES = int(os.getenv("MAX_HTML_BYTES", "800000"))  # Reducido de 1.2MB a 800KB
CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "2"))   # Más agresivo: 3→2
READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "5"))        # Más agresivo: 6→5
WRITE_TIMEOUT = float(os.getenv("WRITE_TIMEOUT", "5"))      # Más agresivo: 6→5
POOL_TIMEOUT = float(os.getenv("POOL_TIMEOUT", "2"))       # Más agresivo: 3→2
MAX_CONNS = int(os.getenv("MAX_CONNS", "20"))              # Reducido para Render: 30→20
MAX_KEEPALIVE = int(os.getenv("MAX_KEEPALIVE", "10"))      # Reducido: 20→10

try:
    import h2  # noqa: F401
    from cachetools import TTLCache
    _robot_cache = TTLCache(maxsize=100, ttl=3600)  # Cache 1 hora
    HTTP2 = True
except ImportError:
    HTTP2 = False
    _robot_cache = {}

def _robots_for(url: str) -> robotparser.RobotFileParser:
    parsed = urlparse(url)
    host = parsed.netloc
    if host in _robot_cache:
        return _robot_cache[host]
    rp = robotparser.RobotFileParser()
    scheme = parsed.scheme or "https"
    rp.set_url(f"{scheme}://{host}/robots.txt")
    try:
        rp.read()
    except Exception:
        pass
    _robot_cache[host] = rp
    return rp

async def _read_capped(resp: httpx.Response, byte_cap: int) -> str:
    """Lee la respuesta hasta byte_cap y corta (más rápido que cargar todo)."""
    chunks = []
    total = 0
    async for chunk in resp.aiter_bytes():
        chunks.append(chunk)
        total += len(chunk)
        if total >= byte_cap:
            break
    try:
        content = b"".join(chunks)
        # httpx hace autodetect del encoding si usás .text, pero ya tenemos bytes
        return content.decode(resp.encoding or "utf-8", errors="ignore")
    except Exception:
        return ""

async def fetch_html(
    client: httpx.AsyncClient,
    url: str,
    respect_robots: bool = True,
    timeout: float = 10.0,
) -> Tuple[str, Optional[str]]:
    """
    Devuelve (url, html) o (url, None) si no se pudo obtener.
    Tope de bytes + timeouts agresivos + follow_redirects.
    """
    try:
        if respect_robots:
            rp = _robots_for(url)
            try:
                ua = DEFAULT_HEADERS.get("User-Agent", "*")
                if hasattr(rp, "can_fetch") and not (rp.can_fetch(ua, url) or rp.can_fetch("*", url)):
                    return (url, None)
            except Exception:
                pass

        resp = await client.get(url, timeout=timeout)
        resp.raise_for_status()
        html = await _read_capped(resp, MAX_HTML_BYTES)
        return (url, html if html else None)
    except Exception:
        return (url, None)

async def fetch_many(
    urls: List[str],
    respect_robots: bool = True,
    timeout: float = 10.0,
) -> List[Tuple[str, Optional[str]]]:
    """
    Ejecuta peticiones en paralelo y devuelve [(url, html|None), ...].
    """
    limits = httpx.Limits(max_connections=MAX_CONNS, max_keepalive_connections=MAX_KEEPALIVE)
    timeouts = httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=WRITE_TIMEOUT, pool=POOL_TIMEOUT)
    async with httpx.AsyncClient(
        http2=HTTP2,
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        limits=limits,
        timeout=timeouts,
    ) as client:
        tasks = [fetch_html(client, u, respect_robots=respect_robots, timeout=timeout) for u in urls]
        return await asyncio.gather(*tasks)

def discover_feeds_from_html(base_url: str, html: str) -> List[str]:
    feeds = set()
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("link", attrs={"type": ["application/rss+xml", "application/atom+xml"]}):
        href = link.get("href")
        if href:
            feeds.add(urljoin(base_url, href))
    return list(feeds)

def extract_internal_links(base_url: str, html: str, max_links: int = 200) -> List[str]:
    if not html:
        return []
    base = httpx.URL(base_url)
    host = base.host
    soup = BeautifulSoup(html, "lxml")
    out: List[str] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        try:
            abs_url = str(base.join(href))
        except Exception:
            continue
        u = httpx.URL(abs_url)
        if u.host and host and u.host.endswith(host.split(".", 1)[-1]):
            if abs_url not in seen:
                seen.add(abs_url); out.append(abs_url)
        if len(out) >= max_links:
            break
    return out
