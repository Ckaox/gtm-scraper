import re
from urllib.parse import urljoin, urlparse
import tldextract

DEFAULT_PATHS = ["/", "/about", "/company", "/product", "/platform", "/solutions",
                 "/blog", "/news", "/press", "/careers", "/jobs"]

BLOCKLIST_PATTERNS = re.compile(r"(privacy|terms|cookie|login|signin|signup|account)", re.I)

def absolutize(base: str, path: str) -> str:
    return urljoin(base, path)

def base_from_domain(domain: str) -> str:
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    return f"https://{domain}"

def discover_candidate_urls(base_url: str, include_paths=None):
    paths = include_paths or DEFAULT_PATHS
    base = base_url.rstrip("/")
    return [absolutize(base, p) for p in paths]

def domain_of(url: str) -> str:
    parts = tldextract.extract(url)
    return f"{parts.domain}.{parts.suffix}" if parts.suffix else parts.domain

def looks_blocklisted(url: str) -> bool:
    return bool(BLOCKLIST_PATTERNS.search(url))

def normalize_company_name(name: str | None) -> str | None:
    if not name:
        return None
    name = re.sub(r"\s+", " ", name).strip()
    # corta sufijos comunes (opc)
    name = re.sub(r"\b(inc|llc|s\.a\.|s\.l\.|ltd|corp|co)\.?$", "", name, flags=re.I).strip()
    return name or None
