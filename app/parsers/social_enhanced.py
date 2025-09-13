#!/usr/bin/env python3
"""
Enhanced Social Extraction - Testing module
Mejora la extracción de redes sociales con metadata y más plataformas
"""

from bs4 import BeautifulSoup
import json
from typing import Dict


def extract_enhanced_social(html: str) -> Dict[str, str]:
    """
    Extrae redes sociales de HTML usando múltiples estrategias
    - Links directos en <a> tags
    - Meta tags con contenido social
    - JSON-LD structured data
    - Más plataformas: Discord, WhatsApp, Telegram, etc.
    """
    social_data = {}
    if not html:
        return social_data
    
    soup = BeautifulSoup(html, "lxml")
    
    # ESTRATEGIA 1: Links directos (mejorado)
    direct_links = _extract_direct_social_links(soup)
    social_data.update(direct_links)
    
    # ESTRATEGIA 2: Meta tags
    meta_social = _extract_social_from_meta(soup)
    # Solo agregar si no existe ya
    social_data.update({k: v for k, v in meta_social.items() if k not in social_data})
    
    # ESTRATEGIA 3: JSON-LD structured data
    if len(social_data) < 5:  # Solo si necesitamos más
        structured_social = _extract_social_from_json_ld(soup)
        social_data.update({k: v for k, v in structured_social.items() if k not in social_data})
    
    return social_data


def _extract_direct_social_links(soup) -> Dict[str, str]:
    """Extrae links sociales directos de tags <a>"""
    social_data = {}
    
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"].strip()
        if not href:
            continue
        
        href_lower = href.lower()
        
        # Skip obvious non-social pages
        if any(skip in href_lower for skip in [
            "privacy", "privacidad", "terms", "condiciones", 
            "cookies", "legal", "contact", "contacto", "notices",
            "policy", "politica", "about/legal", "support", 
            "help", "ayuda", "faq", "aviso", "disclaimer",
            "share", "login", "oauth", "auth", "intent"
        ]):
            continue
            
        # Skip obviously wrong URLs
        if len(href) > 200 or ("?" in href and len(href.split("?")[1]) > 50):
            continue
        
        # Detect social platforms (enhanced)
        if "linkedin.com/company" in href_lower and "linkedin" not in social_data:
            social_data["linkedin"] = href
        elif "linkedin.com/in/" in href_lower and "linkedin" not in social_data:
            social_data["linkedin"] = href
        elif "facebook.com" in href_lower and "facebook" not in social_data:
            if "/pages/" in href_lower or (href_lower.count("/") >= 3 and "sharer" not in href_lower):
                social_data["facebook"] = href
        elif ("twitter.com" in href_lower or "x.com" in href_lower) and "twitter" not in social_data:
            social_data["twitter"] = href
        elif "instagram.com" in href_lower and "instagram" not in social_data:
            social_data["instagram"] = href
        elif "youtube.com" in href_lower and "youtube" not in social_data:
            if any(x in href_lower for x in ["/channel/", "/c/", "/user/", "/@", "/watch"]):
                social_data["youtube"] = href
        elif "tiktok.com" in href_lower and "tiktok" not in social_data:
            social_data["tiktok"] = href
        elif "github.com" in href_lower and "github" not in social_data:
            social_data["github"] = href
        # Additional platforms
        elif "discord.gg" in href_lower and "discord" not in social_data:
            social_data["discord"] = href
        elif "twitch.tv" in href_lower and "twitch" not in social_data:
            social_data["twitch"] = href
        elif "reddit.com/r/" in href_lower and "reddit" not in social_data:
            social_data["reddit"] = href
        elif "pinterest.com" in href_lower and "pinterest" not in social_data:
            social_data["pinterest"] = href
        elif ("whatsapp.com" in href_lower or "wa.me" in href_lower) and "whatsapp" not in social_data:
            social_data["whatsapp"] = href
        elif ("telegram.me" in href_lower or "t.me" in href_lower) and "telegram" not in social_data:
            social_data["telegram"] = href
    
    return social_data


def _extract_social_from_meta(soup) -> Dict[str, str]:
    """Extrae links sociales de meta tags"""
    social_data = {}
    
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        content = meta.get('content', '')
        if not content:
            continue
            
        content_lower = content.lower()
        
        # Look for social URLs in meta content
        if 'facebook.com' in content_lower and 'facebook' not in social_data:
            social_data['facebook'] = content
        elif ('twitter.com' in content_lower or 'x.com' in content_lower) and 'twitter' not in social_data:
            social_data['twitter'] = content
        elif 'instagram.com' in content_lower and 'instagram' not in social_data:
            social_data['instagram'] = content
        elif 'linkedin.com' in content_lower and 'linkedin' not in social_data:
            social_data['linkedin'] = content
        elif 'youtube.com' in content_lower and 'youtube' not in social_data:
            social_data['youtube'] = content
    
    return social_data


def _extract_social_from_json_ld(soup) -> Dict[str, str]:
    """Extrae links sociales de JSON-LD structured data"""
    social_data = {}
    
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            if not script.string:
                continue
                
            data = json.loads(script.string)
            
            # Look for sameAs property (common for organizations)
            if isinstance(data, dict) and 'sameAs' in data:
                same_as = data['sameAs']
                if isinstance(same_as, list):
                    for url in same_as:
                        url_lower = url.lower()
                        if 'facebook.com' in url_lower and 'facebook' not in social_data:
                            social_data['facebook'] = url
                        elif ('twitter.com' in url_lower or 'x.com' in url_lower) and 'twitter' not in social_data:
                            social_data['twitter'] = url
                        elif 'instagram.com' in url_lower and 'instagram' not in social_data:
                            social_data['instagram'] = url
                        elif 'linkedin.com' in url_lower and 'linkedin' not in social_data:
                            social_data['linkedin'] = url
                        elif 'youtube.com' in url_lower and 'youtube' not in social_data:
                            social_data['youtube'] = url
                            
        except json.JSONDecodeError:
            continue  # Skip malformed JSON
        except Exception:
            continue  # Skip any other errors
    
    return social_data


if __name__ == "__main__":
    # Test con algunos sitios
    import asyncio
    from app.fetch import fetch_many
    from app.util import smart_domain_resolver
    
    async def test_enhanced_social():
        test_domains = ['github.com', 'netflix.com', 'shopify.com']
        
        for domain in test_domains:
            print(f'\n=== Testing {domain} ===')
            
            base = smart_domain_resolver(domain, timeout=3)
            result = await fetch_many([base], respect_robots=False, timeout=2)
            html = result[0][1] if result and result[0] else None
            
            if html:
                social_data = extract_enhanced_social(html)
                
                print(f'Social platforms found: {len(social_data)}')
                for platform, url in social_data.items():
                    print(f'  {platform}: {url}')
            else:
                print('Failed to fetch HTML')
            
            print('-' * 50)
    
    asyncio.run(test_enhanced_social())