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
        # Si falla la lectura, dejamos el parser “vacío” en cache para no reintentar.
        pass
    _robot_cache[host] = rp
    return rp


async def fetch_html(
    client: httpx.AsyncClient,
    url: str,
    respect_robots: bool = True,
    timeout: float = 10.0,
) -> Tuple[str, Optional[str]]:
    """
    Devuelve (url, html) o (url, None) si no se pudo obtener.
    Captura errores y no propaga excepciones.
    """
    try:
        if respect_robots:
            rp = _robots_for(url)
            try:
                ua = DEFAULT_HEADERS.get("User-Agent", "*")
                # Intentamos con nuestro UA y con '*' por compatibilidad
                if hasattr(rp, "can_fetch") and not (rp.can_fetch(ua, url) or rp.can_fetch("*", url)):
                    return (url, None)
            except Exception:
                # Si algo falla evaluando robots, no bloqueamos (fail-open)
                pass

        resp = await client.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return (url, resp.text)
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
    async with httpx.AsyncClient(http2=HTTP2, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
        tasks = [
            fetch_html(client, u, respect_robots=respect_robots, timeout=timeout)
            for u in urls
        ]
        results = await asyncio.gather(*tasks)
        return results


def discover_feeds_from_html(base_url: str, html: str) -> List[str]:
    """
    Descubre enlaces a feeds (RSS/Atom) en el HTML.
    """
    feeds = set()
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("link", attrs={"type": ["application/rss+xml", "application/atom+xml"]}):
        href = link.get("href")
        if href:
            # Sin .human_repr(): usamos urljoin o str(httpx.URL(...))
            feeds.add(urljoin(base_url, href))
    return list(feeds)


def extract_internal_links(base_url: str, html: str, max_links: int = 200) -> List[str]:
    """
    Devuelve enlaces internos únicos (mismo dominio o subdominios) encontrados en la página.
    """
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
            abs_url = str(base.join(href))  # sin .human_repr()
        except Exception:
            continue

        u = httpx.URL(abs_url)
        # mismo dominio o subdominio (permitimos subdominios)
        if u.host and host:
            # Coincidencia por TLD+SLD básicos (ej.: ejemplo.com)
            if u.host.endswith(host.split(".", 1)[-1]):
                if abs_url not in seen:
                    seen.add(abs_url)
                    out.append(abs_url)

        if len(out) >= max_links:
            break

    return out
