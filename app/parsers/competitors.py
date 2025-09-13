# app/parsers/competitors.py
import re
from typing import List, Set
from bs4 import BeautifulSoup

# Mapeo de industrias a competitors conocidos
INDUSTRY_COMPETITORS = {
    "Salud (Hospitales y Clínicas)": [
        "epic.com", "cerner.com", "allscripts.com", "athenahealth.com"
    ],
    "Tecnología y Software (SaaS/Cloud)": [
        "salesforce.com", "hubspot.com", "slack.com", "zoom.us", "dropbox.com",
        "atlassian.com", "servicenow.com", "workday.com"
    ],
    "Fintech y Pagos": [
        "stripe.com", "square.com", "paypal.com", "adyen.com", "klarna.com"
    ],
    "Comercio Electrónico (E-commerce)": [
        "shopify.com", "magento.com", "woocommerce.com", "bigcommerce.com"
    ],
    "Marketing": [
        "mailchimp.com", "constantcontact.com", "sendgrid.com", "marketo.com"
    ],
    "Recursos Humanos y Staffing": [
        "workday.com", "bamboohr.com", "namely.com", "zenefits.com"
    ]
}

def detect_competitors_from_content(html: str, detected_industry: str = None) -> List[str]:
    """
    Detecta competidores mencionados en el contenido de la página.
    Muy rápido - solo busca menciones de dominios conocidos.
    """
    if not html:
        return []
    
    text = BeautifulSoup(html, "lxml").get_text().lower()
    competitors_found = set()
    
    # Si conocemos la industria, buscar competitors específicos
    if detected_industry and detected_industry in INDUSTRY_COMPETITORS:
        industry_competitors = INDUSTRY_COMPETITORS[detected_industry]
        for competitor in industry_competitors:
            # Buscar menciones del dominio (sin .com para ser más flexible)
            domain_base = competitor.replace(".com", "").replace(".io", "").replace(".co", "")
            if domain_base in text:
                competitors_found.add(competitor)
    
    # Buscar menciones generales de grandes players tecnológicos
    big_tech = [
        "salesforce", "hubspot", "slack", "zoom", "microsoft", "google", 
        "amazon", "oracle", "sap", "adobe", "shopify", "stripe"
    ]
    
    for tech in big_tech:
        if tech in text:
            # Intentar reconstruir el dominio más probable
            if "salesforce" in tech:
                competitors_found.add("salesforce.com")
            elif "hubspot" in tech:
                competitors_found.add("hubspot.com")
            elif "shopify" in tech:
                competitors_found.add("shopify.com")
            # Agregar más mappings según necesidad
    
    return list(competitors_found)[:5]  # Máximo 5 para no sobrecargar

def detect_integration_mentions(html: str) -> List[str]:
    """
    Detecta integraciones mencionadas que pueden indicar el stack tecnológico
    y competidores indirectos.
    """
    if not html:
        return []
    
    text = BeautifulSoup(html, "lxml").get_text().lower()
    integrations = []
    
    # Patrones de integración comunes
    integration_patterns = [
        r'integra(?:te|tion)s?\s+with\s+([a-z]+)',
        r'conecta\s+con\s+([a-z]+)',
        r'compatible\s+with\s+([a-z]+)',
        r'works\s+with\s+([a-z]+)'
    ]
    
    for pattern in integration_patterns:
        matches = re.findall(pattern, text, re.I)
        integrations.extend(matches)
    
    # Filtrar y limpiar
    cleaned_integrations = []
    for integration in integrations:
        if len(integration) > 3 and integration not in ["with", "the", "and", "our"]:
            cleaned_integrations.append(integration.title())
    
    return list(set(cleaned_integrations))[:8]  # Máximo 8, deduplicadas