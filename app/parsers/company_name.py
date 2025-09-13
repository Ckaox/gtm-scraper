# app/parsers/company_name.py
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional


def extract_company_name_from_html(html: str, domain: str, fallback_name: Optional[str] = None) -> Optional[str]:
    """
    Extract company name from multiple sources with fallback options.
    Priority order:
    1. JSON-LD Organization name
    2. Meta property og:site_name
    3. Page title (cleaned)
    4. H1 tag (if looks like company name)
    5. Domain name (cleaned)
    6. Fallback provided name
    """
    if not html:
        result = _clean_domain_name(domain) or fallback_name
        return result
    
    soup = BeautifulSoup(html, "lxml")
    
    # 1. JSON-LD Organization name
    json_ld_name = _extract_from_json_ld(soup)
    if json_ld_name:
        return json_ld_name
    
    # 2. Meta property og:site_name
    og_site_name = _extract_from_og_site_name(soup)
    if og_site_name:
        return og_site_name
    
    # 3. Page title (cleaned)
    title_name = _extract_from_title(soup, domain)
    if title_name:
        return title_name
    
    # 4. H1 tag (if looks like company name)
    h1_name = _extract_from_h1(soup)
    if h1_name:
        return h1_name
    
    # 5. Domain name (cleaned)
    domain_name = _clean_domain_name(domain)
    if domain_name:
        return domain_name
    
    # 6. Fallback
    return fallback_name


def _extract_from_json_ld(soup: BeautifulSoup) -> Optional[str]:
    """Extract company name from JSON-LD structured data."""
    try:
        import json
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for item in items:
                    if isinstance(item, dict) and item.get("@type") in ["Organization", "LocalBusiness", "Corporation"]:
                        name = item.get("name")
                        if name and isinstance(name, str) and len(name.strip()) > 0:
                            return name.strip()
            except (json.JSONDecodeError, TypeError):
                continue
    except Exception:
        pass
    return None


def _extract_from_og_site_name(soup: BeautifulSoup) -> Optional[str]:
    """Extract company name from Open Graph site_name."""
    try:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            name = og_site["content"].strip()
            if name and not _is_generic_name(name):
                # Apply title cleaning to og:site_name as well
                cleaned = _clean_title_for_company_name(name)
                return cleaned if cleaned else name
    except Exception:
        pass
    return None


def _extract_from_title(soup: BeautifulSoup, domain: str) -> Optional[str]:
    """Extract company name from page title, cleaning common patterns."""
    try:
        title_tag = soup.find("title")
        if not title_tag or not title_tag.string:
            return None
        
        title = title_tag.string.strip()
        if not title:
            return None
        
        # Clean common title patterns
        cleaned = _clean_title_for_company_name(title)
        
        if cleaned and not _is_generic_name(cleaned) and len(cleaned) >= 2:
            return cleaned
    except Exception:
        pass
    return None


def _extract_from_h1(soup: BeautifulSoup) -> Optional[str]:
    """Extract company name from H1 if it looks like a company name."""
    try:
        h1_tags = soup.find_all("h1")
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            if text and _looks_like_company_name(text):
                return text
    except Exception:
        pass
    return None


def _clean_domain_name(domain: str) -> Optional[str]:
    """Clean domain name to extract potential company name."""
    try:
        # Remove protocol and www
        clean_domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
        
        # Get domain without TLD
        parts = clean_domain.split(".")
        if len(parts) >= 2:
            base_name = parts[0]
            
            # Clean and capitalize
            # Remove hyphens and underscores, capitalize words
            name = base_name.replace("-", " ").replace("_", " ")
            name = " ".join(word.capitalize() for word in name.split())
            
            if len(name) >= 2:
                return name
    except Exception:
        pass
    return None


def _clean_title_for_company_name(title: str) -> Optional[str]:
    """Clean page title to extract company name."""
    # Common separators and patterns to remove
    separators = ["|", "-", "–", "—", ":", "•", "»", ">"]
    
    # Split by separators and find the most likely company name part
    parts = [title]
    for sep in separators:
        if sep in title:
            parts = title.split(sep)
            break
    
    # Look for the part that looks most like a company name
    candidates = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Remove common non-company words
        if _is_generic_name(part):
            continue
        
        # Clean domain extensions from company names
        part = re.sub(r'\.(com|org|net|es|co\.uk)$', '', part, flags=re.IGNORECASE)
        
        # Prefer shorter, cleaner parts that don't contain common website words
        website_words = ["home", "inicio", "welcome", "bienvenido", "página", "page", "sitio", "site", "web", "oficial", "official"]
        if not any(word in part.lower() for word in website_words):
            candidates.append(part)
    
    if candidates:
        # Return the first non-generic candidate (usually leftmost = company name)
        return candidates[0]
    
    return None


def _looks_like_company_name(text: str) -> bool:
    """Check if text looks like a company name."""
    if len(text) < 2 or len(text) > 100:
        return False
    
    # Should not contain common website/page words
    website_words = [
        "welcome", "bienvenido", "home", "inicio", "página", "page",
        "about", "acerca", "contact", "contacto", "services", "servicios"
    ]
    
    if any(word in text.lower() for word in website_words):
        return False
    
    # Should contain letters
    if not re.search(r'[a-zA-Z]', text):
        return False
    
    return True


def _is_generic_name(name: str) -> bool:
    """Check if name is too generic to be useful."""
    generic_names = [
        "home", "inicio", "welcome", "bienvenido", "website", "sitio web",
        "official site", "sitio oficial", "loading", "cargando", "untitled",
        "sin título", "page", "página", "default", "por defecto"
    ]
    
    return name.lower().strip() in generic_names or len(name.strip()) < 2