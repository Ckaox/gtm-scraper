# app/parsers/linkedin.py
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup

def parse_linkedin_company(html: str) -> Dict[str, any]:
    """
    Extrae información valiosa de una página de LinkedIn de empresa.
    Optimizado para ser rápido y no sobrecargar el scraping.
    """
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "lxml")
    info = {}
    
    # Employee count (muy valioso para GTM)
    employee_text = soup.get_text()
    employee_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*empleados?', employee_text, re.I)
    if not employee_match:
        employee_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*employees?', employee_text, re.I)
    
    if employee_match:
        count_str = employee_match.group(1).replace(",", "")
        info["employee_count"] = int(count_str)
        info["company_size_segment"] = get_company_size_segment(int(count_str))
    
    # Company description (solo primeras 300 chars)
    desc_elem = soup.select_one('[data-test-id="about-us-description"]')
    if desc_elem:
        desc = desc_elem.get_text(strip=True)
        info["description"] = desc[:300] + "..." if len(desc) > 300 else desc
    
    # Industry from LinkedIn (often more accurate than our detection)
    industry_elem = soup.select_one('[data-test-id="about-us-industry"]')
    if industry_elem:
        info["linkedin_industry"] = industry_elem.get_text(strip=True)
    
    return info

def extract_linkedin_url_from_html(html: str, domain: str) -> Optional[str]:
    """
    Busca el URL de LinkedIn de la empresa en el HTML.
    Muy útil para encontrar automáticamente el LinkedIn.
    """
    if not html:
        return None
    
    soup = BeautifulSoup(html, "lxml")
    
    # Buscar enlaces a LinkedIn
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "linkedin.com/company/" in href:
            return a["href"]
    
    # Buscar en JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "{}")
            if isinstance(data, dict):
                same_as = data.get("sameAs", [])
                if isinstance(same_as, str):
                    same_as = [same_as]
                for url in same_as:
                    if "linkedin.com/company/" in url.lower():
                        return url
        except:
            continue
    
    return None

def get_company_size_segment(employee_count: Optional[int]) -> Optional[str]:
    """
    Segmenta empresas por tamaño - muy útil para GTM targeting.
    """
    if not employee_count:
        return None
    
    if employee_count <= 10:
        return "Startup (1-10)"
    elif employee_count <= 50:
        return "Small (11-50)"
    elif employee_count <= 200:
        return "Medium (51-200)"
    elif employee_count <= 1000:
        return "Large (201-1000)"
    else:
        return "Enterprise (1000+)"

def analyze_company_maturity_simple(employee_count: Optional[int], html: str) -> Dict[str, any]:
    """
    Análisis rápido de madurez de empresa basado en indicadores simples.
    """
    maturity = {"level": "Unknown", "indicators": []}
    
    text = BeautifulSoup(html, "lxml").get_text().lower()
    
    # Basado en employee count
    if employee_count:
        if employee_count <= 10:
            maturity["level"] = "Early Startup"
            maturity["indicators"].append(f"Small team ({employee_count} employees)")
        elif employee_count <= 100:
            maturity["level"] = "Growing Startup"
            maturity["indicators"].append(f"Mid-size team ({employee_count} employees)")
        elif employee_count <= 1000:
            maturity["level"] = "Scale-up"
            maturity["indicators"].append(f"Large team ({employee_count} employees)")
        else:
            maturity["level"] = "Established"
            maturity["indicators"].append(f"Enterprise size ({employee_count} employees)")
    
    # Indicadores adicionales rápidos
    if any(word in text for word in ["founded", "startup", "we are building"]):
        if maturity["level"] == "Unknown":
            maturity["level"] = "Early Stage"
        maturity["indicators"].append("Startup language detected")
    
    if any(word in text for word in ["series a", "series b", "funding", "investors"]):
        maturity["indicators"].append("Funding mentions")
    
    if any(word in text for word in ["ipo", "public company", "nasdaq", "nyse"]):
        maturity["level"] = "Public Company"
        maturity["indicators"].append("Public company indicators")
    
    return maturity