#!/usr/bin/env python3
"""
Context Summary Parser - Clean implementation
Extrae un resumen inteligente del contenido de la página para outbound sales
"""

from bs4 import BeautifulSoup
import re
from typing import Optional


def extract_context_summary(html: str, company_name: str = "", max_length: int = 200) -> Optional[str]:
    """
    Extrae un resumen inteligente del contexto de la empresa
    Prioriza: meta description > about sections > main content > first paragraph
    """
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # PRIORIDAD 1: Meta description (más confiable)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc = meta_desc.get('content', '').strip()
            if desc and len(desc) > 20:  # Descartar descripciones muy cortas
                cleaned = _clean_and_truncate(desc, max_length)
                if cleaned:  # Solo devolver si la limpieza fue exitosa
                    return cleaned
        
        # PRIORIDAD 2: Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            desc = og_desc.get('content', '').strip()
            if desc and len(desc) > 20:
                cleaned = _clean_and_truncate(desc, max_length)
                if cleaned:
                    return cleaned
        
        # PRIORIDAD 3: About sections (muy específico para empresas)
        about_selectors = [
            'section[class*="about"]',
            'div[class*="about"]',
            'section[class*="company"]',
            'div[class*="company"]',
            'section[id*="about"]',
            'div[id*="about"]',
            '.hero-description',
            '.company-description',
            '.intro-text'
        ]
        
        for selector in about_selectors:
            about_section = soup.select_one(selector)
            if about_section:
                text = about_section.get_text(separator=' ', strip=True)
                if text and len(text) > 30:
                    # Buscar primer párrafo significativo
                    sentences = _split_into_sentences(text)
                    summary = _build_summary_from_sentences(sentences, max_length)
                    if summary:
                        return summary
        
        # PRIORIDAD 4: Hero sections y main content
        hero_selectors = [
            '.hero',
            '.hero-content',
            '.banner-content',
            '.intro',
            '.main-content p:first-of-type',
            'main p:first-of-type',
            '.content p:first-of-type'
        ]
        
        for selector in hero_selectors:
            hero_section = soup.select_one(selector)
            if hero_section:
                text = hero_section.get_text(separator=' ', strip=True)
                if text and len(text) > 30:
                    sentences = _split_into_sentences(text)
                    summary = _build_summary_from_sentences(sentences, max_length)
                    if summary:
                        return summary
        
        # PRIORIDAD 5: Primer párrafo significativo del body
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Filtrar párrafos de navegación o muy cortos
            if (text and len(text) > 50 and 
                not _is_navigation_text(text) and
                not _is_cookie_text(text)):
                return _clean_and_truncate(text, max_length)
        
        # PRIORIDAD 6: Fallback - primer texto significativo
        all_text = soup.get_text(separator=' ', strip=True)
        if all_text:
            sentences = _split_into_sentences(all_text)
            # Buscar primer frase que mencione la empresa o sea descriptiva
            for sentence in sentences[:10]:  # Solo las primeras 10 frases
                if (len(sentence) > 40 and 
                    (company_name.lower() in sentence.lower() if company_name else True) and
                    not _is_navigation_text(sentence)):
                    return _clean_and_truncate(sentence, max_length)
        
        return None
        
    except Exception as e:
        print(f"Error extracting context summary: {e}")
        return None


def _clean_and_truncate(text: str, max_length: int) -> str:
    """
    Limpia el texto y lo trunca de manera inteligente
    """
    # Limpiar caracteres extraños y espacios múltiples
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Filtrar caracteres no ASCII y caracteres raros (más estricto)
    text = re.sub(r'[^\x00-\x7F]', '', text)  # Solo ASCII
    text = re.sub(r'[^\w\s.,;:!?()áéíóúñü-]', '', text, flags=re.IGNORECASE)
    
    # Si el texto resultante es muy corto o vacío, devolver None
    if len(text.strip()) < 20:
        return None
    
    if len(text) <= max_length:
        return text
    
    # Truncar en palabra completa
    truncated = text[:max_length].rsplit(' ', 1)[0]
    
    # Si termina con puntuación, dejarlo; si no, agregar "..."
    if truncated and truncated[-1] in '.!?':
        return truncated
    else:
        return truncated + "..."


def _split_into_sentences(text: str) -> list:
    """
    Divide texto en oraciones de manera inteligente
    """
    # Dividir por puntos, exclamaciones y interrogaciones
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


def _build_summary_from_sentences(sentences: list, max_length: int) -> Optional[str]:
    """
    Construye un resumen combinando oraciones hasta llegar al límite
    """
    if not sentences:
        return None
    
    summary = ""
    for sentence in sentences:
        # Agregar primera oración siempre
        if not summary:
            summary = sentence
        else:
            # Verificar si cabe la siguiente oración
            potential = summary + ". " + sentence
            if len(potential) <= max_length:
                summary = potential
            else:
                break
    
    return _clean_and_truncate(summary, max_length) if summary else None


def _is_navigation_text(text: str) -> bool:
    """
    Detecta si el texto es de navegación/menú
    """
    nav_keywords = [
        'menu', 'navigation', 'home', 'about', 'contact', 'login', 'sign up',
        'products', 'services', 'blog', 'news', 'search', 'cart', 'account',
        'terms', 'privacy', 'cookie', 'skip to content', 'toggle'
    ]
    
    text_lower = text.lower()
    nav_count = sum(1 for keyword in nav_keywords if keyword in text_lower)
    
    # Si tiene muchas palabras de navegación o es muy corto, es navegación
    return nav_count > 2 or len(text.split()) < 5


def _is_cookie_text(text: str) -> bool:
    """
    Detecta si el texto es sobre cookies/legal
    """
    cookie_keywords = ['cookie', 'privacy policy', 'terms of service', 'gdpr', 'consent']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in cookie_keywords)