# app/parsers/seo_metrics.py
from bs4 import BeautifulSoup
from typing import Dict, List
import re

def extract_seo_metrics(html: str, url: str, request_time_ms: int = None) -> Dict[str, any]:
    """
    Extrae métricas SEO comprehensivas y rápidas.
    """
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "lxml")
    metrics = {}
    
    # Basic SEO metrics
    title = soup.find("title")
    if title and title.string:
        metrics["meta_title_length"] = len(title.string.strip())
    
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        metrics["meta_description_length"] = len(meta_desc["content"].strip())
    
    # Structured data presence
    has_structured = bool(
        soup.find("script", type="application/ld+json") or 
        soup.find(attrs={"itemtype": True}) or
        soup.find(attrs={"itemscope": True})
    )
    metrics["has_structured_data"] = has_structured
    
    # Sitemap link presence
    sitemap_link = soup.find("link", attrs={"rel": "sitemap"})
    metrics["has_sitemap_link"] = bool(sitemap_link)
    
    # Page load time (if provided)
    if request_time_ms is not None:
        metrics["page_load_time_ms"] = request_time_ms
    
    # Heading structure
    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")
    metrics["h1_count"] = len(h1_tags)
    metrics["h2_count"] = len(h2_tags)
    
    # Image optimization
    images = soup.find_all("img")
    images_without_alt = [img for img in images if not img.get("alt")]
    metrics["image_alt_missing"] = len(images_without_alt)
    
    # Link analysis
    all_links = soup.find_all("a", href=True)
    internal_links = [link for link in all_links if _is_internal_link(link["href"], url)]
    external_links = [link for link in all_links if _is_external_link(link["href"], url)]
    
    metrics["internal_links_count"] = len(internal_links)
    metrics["external_links_count"] = len(external_links)
    
    # Page size estimation (rough)
    page_size_bytes = len(html.encode('utf-8'))
    metrics["page_size_kb"] = round(page_size_bytes / 1024, 2)
    
    return metrics


def _is_internal_link(href: str, base_url: str) -> bool:
    """Check if link is internal to the same domain."""
    if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
        return False
    if href.startswith('/'):
        return True
    if href.startswith('http'):
        try:
            from urllib.parse import urlparse
            href_domain = urlparse(href).netloc.lower()
            base_domain = urlparse(base_url).netloc.lower()
            return href_domain == base_domain
        except:
            return False
    return True


def _is_external_link(href: str, base_url: str) -> bool:
    """Check if link is external."""
    if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
        return False
    if href.startswith('/'):
        return False
    if href.startswith('http'):
        try:
            from urllib.parse import urlparse
            href_domain = urlparse(href).netloc.lower()
            base_domain = urlparse(base_url).netloc.lower()
            return href_domain != base_domain
        except:
            return False
    return False