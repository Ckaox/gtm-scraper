import re
from urllib.parse import urljoin, urlparse
import tldextract
import httpx
from typing import Optional

DEFAULT_PATHS = [  # fallback si falla la home
    "/", "/about", "/company", "/product", "/platform", "/solutions",
    "/blog", "/news", "/press", "/careers", "/jobs",
    # Páginas de contacto y calendario (para detectar CRMs como GoHighLevel)
    "/contact", "/contacto", "/call", "/llamada", "/calendar", "/calendario", 
    "/book", "/reservar", "/meeting", "/reunion", "/appointment", "/cita",
    "/schedule", "/agendar", "/demo", "/consultation", "/consultoria",
    "/discovery", "/descubrimiento", "/free-call", "/llamada-gratuita",
    "/get-started", "/comenzar", "/quote", "/cotizar", "/booking", "/forms",
    # Páginas adicionales para detectar más tecnologías
    "/login", "/signup", "/register", "/account", "/dashboard", "/admin",
    "/checkout", "/cart", "/shop", "/store", "/tienda", "/comprar",
    "/support", "/help", "/ayuda", "/soporte", "/faq", "/pricing", "/precios",
    "/features", "/caracteristicas", "/tools", "/herramientas", "/integrations",
    "/api", "/developers", "/documentation", "/docs", "/resources", "/recursos",
    "/case-studies", "/casos-de-exito", "/testimonials", "/testimonios",
    "/partners", "/socios", "/affiliates", "/afiliados", "/resellers",
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
    "careers": ["careers", "jobs", "empleo", "empleos", "trabajo", "talento", "carreras", "trabaja", "join-us"],
    "contact": ["contact", "contacto", "call", "llamada", "calendar", "calendario", "book", "reservar", 
               "meeting", "reunion", "appointment", "cita", "schedule", "agendar", "demo", "consultation", 
               "consultoria", "discovery", "descubrimiento", "free-call", "llamada-gratuita"]
}

KEYWORD_WEIGHTS = {
    "careers": 3,
    "product": 3,
    "contact": 2,  # Páginas de contacto tienen prioridad alta para detectar CRMs
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


# Cache para domain resolution (en memoria)
_domain_cache = {}

def smart_domain_resolver(domain: str, timeout: int = 5) -> str:
    """
    Resuelve automáticamente la mejor URL para un dominio probando variaciones.
    MEJORADO para manejar más casos y aumentar success rate.
    
    Args:
        domain: Dominio a resolver (ej: "kaioland.com")
        timeout: Timeout para cada prueba
        
    Returns:
        La mejor URL que funciona, o la URL original si ninguna funciona
    """
    # 🚀 CACHE CHECK - Si ya resolvimos este dominio antes
    if domain in _domain_cache:
        print(f"🚀 Cache hit para {domain}: {_domain_cache[domain]}")
        return _domain_cache[domain]
    
    # Limpiar el dominio
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        clean_domain = parsed.netloc
    else:
        clean_domain = domain.strip().replace("http://", "").replace("https://", "").rstrip("/")
    
    # MEJORA: Más variaciones inteligentes para aumentar success rate
    variations = []
    
    if clean_domain.startswith("www."):
        base_domain = clean_domain[4:]  # Remove www.
        variations = [
            f"https://{clean_domain}",          # Original con www
            f"https://{base_domain}",           # Sin www
        ]
    else:
        base_domain = clean_domain
        variations = [
            f"https://{clean_domain}",          # Original sin www
            f"https://www.{clean_domain}",      # Con www
        ]
    
    # MEJORA: Agregar variaciones de TLD para empresas españolas
    if clean_domain.endswith('.com'):
        base_name = clean_domain[:-4]  # Remove .com
        variations.extend([
            f"https://{base_name}.es",          # .es para España
            f"https://www.{base_name}.es",      # www + .es
        ])
    elif clean_domain.endswith('.es'):
        base_name = clean_domain[:-3]  # Remove .es
        variations.extend([
            f"https://{base_name}.com",         # .com global
            f"https://www.{base_name}.com",     # www + .com
        ])
    
    # Probar cada variación con timeout ultra-agresivo
    for url in variations:
        try:
            # OPTIMIZACIÓN: timeout muy corto y solo HEAD request
            response = httpx.head(url, timeout=timeout//3, follow_redirects=True)  # timeout/3 para ser más agresivos
            if response.status_code in [200, 301, 302, 403]:  # 403 puede ser Cloudflare pero el sitio existe
                # Usar la URL final después de redirects
                final_url = str(response.url).rstrip('/') if hasattr(response, 'url') else url.rstrip('/')
                # 🚀 GUARDAR EN CACHE
                _domain_cache[domain] = final_url
                return final_url
        except Exception:
            continue  # Probar siguiente variación rápidamente
    
    # Si nada funciona, devolver la primera variación y cachear
    fallback_url = f"https://{clean_domain}"
    _domain_cache[domain] = fallback_url
    return fallback_url

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
