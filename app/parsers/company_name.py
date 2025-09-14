"""Simple company name extractor - funcional version"""
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional


def extract_company_name_from_html(html: str, domain: str, fallback_name: Optional[str] = None) -> Optional[str]:
    """Extract company name from HTML using multiple methods."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Method 1: og:site_name
        og_site_name = soup.find("meta", property="og:site_name")
        if og_site_name and og_site_name.get("content"):
            name = og_site_name["content"].strip()
            if name and len(name) >= 2 and not _is_generic_name(name):
                return _clean_company_name(name)
        
        # Method 2: title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            cleaned = _clean_title_for_company_name(title)
            if cleaned and not _is_generic_name(cleaned):
                return cleaned
        
        # Method 3: application-name
        app_name = soup.find("meta", attrs={"name": "application-name"})
        if app_name and app_name.get("content"):
            name = app_name["content"].strip()
            if name and len(name) >= 2 and not _is_generic_name(name):
                return _clean_company_name(name)
        
        # Method 4: headers
        for tag_name in ['h1', 'h2']:
            headers = soup.find_all(tag_name)
            for header in headers:
                text = header.get_text(strip=True)
                if text and 3 <= len(text) <= 50 and not _is_generic_name(text):
                    cleaned = _clean_company_name(text)
                    if cleaned:
                        return cleaned
        
        # Method 5: domain fallback
        if domain:
            parsed = urlparse(f"http://{domain}" if not domain.startswith('http') else domain)
            domain_name = parsed.netloc or parsed.path
            domain_name = domain_name.replace('www.', '')
            name_part = domain_name.split('.')[0]
            if len(name_part) >= 2:
                return name_part.replace('-', ' ').replace('_', ' ').title()
        
        return fallback_name
    except Exception:
        return fallback_name


def _clean_title_for_company_name(title: str) -> Optional[str]:
    """Clean page title to extract company name."""
    if not title:
        return None
    
    # Remove everything after dash, pipe, or colon
    patterns = [r'\s*[-|•]\s*.*$', r'\s*:.*$', r'\s*\|\s*.*$']
    cleaned = title
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
    
    if cleaned and len(cleaned) >= 2:
        return _clean_company_name(cleaned)
    return None


def _clean_company_name(name: str) -> Optional[str]:
    """Clean and standardize company name."""
    if not name:
        return None
    
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    
    # Remove common business suffixes
    suffixes = [r'\s*S\.?L\.?\s*$', r'\s*S\.?A\.?\s*$', r'\s*Ltd\.?\s*$', 
                r'\s*Inc\.?\s*$', r'\s*Corp\.?\s*$', r'\s*LLC\.?\s*$']
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE).strip()
    
    if len(name) >= 2 and not _is_generic_name(name):
        return name
    return None


def _is_generic_name(name: str) -> bool:
    """Check if name is too generic."""
    if not name:
        return True
    
    name_lower = name.lower().strip()
    generic_terms = {
        'home', 'inicio', 'welcome', 'bienvenidos', 'company', 'empresa',
        'official', 'website', 'web', 'site', 'page', 'main', 'index',
        'a', 'an', 'el', 'la', 'the', 'www', 'com'
    }
    
    return (name_lower in generic_terms or 
            len(name_lower) < 2 or 
            name_lower.isdigit())
