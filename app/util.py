import re
from urllib.parse import urljoin, urlparse
import tldextract
import httpx
from typing import Optional

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
    """
    Convierte un dominio en una URL base, probando automáticamente variaciones
    para manejar casos como dominios que requieren 'www.' o diferentes protocolos.
    """
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    # Limpiar el dominio de espacios y protocolos
    clean_domain = domain.strip().replace("http://", "").replace("https://", "").rstrip("/")
    
    return f"https://{clean_domain}"


def smart_domain_resolver(domain: str, timeout: int = 10) -> str:
    """
    Resuelve automáticamente la mejor URL para un dominio probando variaciones.
    Esto soluciona el problema de dominios que requieren 'www.' para funcionar.
    
    Args:
        domain: Dominio a resolver (ej: "kaioland.com")
        timeout: Timeout para cada prueba
        
    Returns:
        La mejor URL que funciona, o la URL original si ninguna funciona
    """
    # Limpiar el dominio
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        clean_domain = parsed.netloc
    else:
        clean_domain = domain.strip().replace("http://", "").replace("https://", "").rstrip("/")
    
    # Variaciones a probar en orden de preferencia
    variations = [
        f"https://{clean_domain}",
        f"https://www.{clean_domain}",
        f"http://{clean_domain}",
        f"http://www.{clean_domain}"
    ]
    
    # Si ya tiene www, prueba sin www también
    if clean_domain.startswith("www."):
        domain_without_www = clean_domain[4:]
        variations = [
            f"https://{clean_domain}",
            f"https://{domain_without_www}",
            f"http://{clean_domain}",
            f"http://{domain_without_www}"
        ]
    
    # Probar cada variación
    for url in variations:
        try:
            response = httpx.head(url, timeout=timeout, follow_redirects=True)
            if response.status_code in [200, 301, 302, 403]:  # 403 puede ser Cloudflare pero el sitio existe
                # Usar la URL final después de redirects
                return str(response.url) if hasattr(response, 'url') else url
        except Exception:
            continue  # Probar siguiente variación
    
    # Si nada funciona, devolver la primera variación (https sin www)
    return f"https://{clean_domain}"

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
