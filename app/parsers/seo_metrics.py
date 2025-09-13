# app/parsers/seo_metrics.py
from bs4 import BeautifulSoup
from typing import Dict, List
import re

def extract_seo_metrics(html: str, url: str) -> Dict[str, any]:
    """
    Extrae métricas SEO básicas muy rápidas (sin llamadas externas).
    """
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "lxml")
    metrics = {}
    
    # Meta title length (factor SEO importante)
    title = soup.find("title")
    if title and title.string:
        metrics["meta_title_length"] = len(title.string.strip())
    
    # Meta description length
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        metrics["meta_description_length"] = len(meta_desc["content"].strip())
    
    # Structured data presence (JSON-LD, Microdata)
    has_structured = bool(
        soup.find("script", type="application/ld+json") or 
        soup.find(attrs={"itemtype": True}) or
        soup.find(attrs={"itemscope": True})
    )
    metrics["has_structured_data"] = has_structured
    
    # Sitemap link presence
    sitemap_link = soup.find("link", attrs={"rel": "sitemap"})
    metrics["has_sitemap_link"] = bool(sitemap_link)
    
    # Quick page load indicators (just presence, not actual measurement)
    load_indicators = []
    
    # CDN usage
    if any(cdn in html.lower() for cdn in ["cdn.", "cloudflare", "amazonaws", "fastly"]):
        load_indicators.append("Uses CDN")
    
    # Image optimization hints
    if "webp" in html.lower():
        load_indicators.append("WebP images")
    
    # Lazy loading
    if "loading=\"lazy\"" in html or "data-src" in html:
        load_indicators.append("Lazy loading")
    
    # Minification hints
    if len(re.findall(r'\s+', html)) < len(html) * 0.1:  # Low whitespace ratio
        load_indicators.append("Likely minified")
    
    metrics["page_load_indicators"] = load_indicators
    
    return metrics