import re
from urllib.parse import urljoin, urlparse
import tldextract

DEFAULT_PATHS = [  # fallback si falla la home
    "/", "/about", "/company", "/product", "/platform", "/solutions",
    "/blog", "/news", "/press", "/careers", "/jobs",
    # ES
    "/es", "/empresa", "/quienes-somos", "/nosotros",
    "/producto", "/productos", "/servicios", "/soluciones",
    "/blog", "/noticias", "/prensa",
    "/empleo", "/empleos", "/trabajo", "/trabaja-con-nosotros", "/carreras", "/talento", "/equipo"
]

PRIORITY_KEYWORDS = {
    "about": ["about", "company", "quienes-somos", "nosotros", "empresa"],
    "product": ["product", "products", "platform", "solution", "solutions", "producto", "productos", "servicios", "soluciones"],
    "blog": ["blog"],
    "news": ["news", "press", "noticias", "prensa"],
    "careers": ["careers", "jobs", "empleo", "empleos", "trabajo", "talento", "carreras", "trabaja", "join-us"]
}

KEYWORD_WEIGHTS = {
    "careers": 3,
    "product": 3,
    "about": 2,
    "news": 2,
    "blog": 1,
}

def keyword_score(url_path: str) -> int:
    path = url_path.lower()
    score = 0
    for bucket, words in PRIORITY_KEYWORDS.items():
        if any(w in path for w in words):
            score += KEYWORD_WEIGHTS.get(bucket, 1)
    # pequeños boosts
    if path.endswith("/") or path.count("/") <= 3:
        score += 1
    return score

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
