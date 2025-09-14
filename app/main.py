# app/app/main.py
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import httpx
import time
import logging

from .schemas import *
from .util import (
    discover_candidate_urls,
    base_from_domain,
    smart_domain_resolver,
    domain_of,
    looks_blocklisted,
    normalize_company_name,
    keyword_score,
)
from .fetch import fetch_many
from .parsers.techstack import detect_tech
from .parsers.news import extract_news_from_html
from .parsers.emails import extract_emails
from .parsers.industry import detectar_principal_y_secundaria
from .parsers.company_name import extract_company_name_from_html
from .parsers.seo_metrics import extract_seo_metrics
from .enrichment import get_enrichment_data

# Logger setup
logger = logging.getLogger(__name__)


# ===========================
# Config optimizada (performance final)
# ===========================
MAX_INTERNAL_LINKS = 40           # Reducido más: 60→40
TOP_CANDIDATES_BY_KEYWORD = 6     # Reducido más: 8→6  
MAX_PAGES_FREE_PLAN = 2           # Reducido más: 3→2
TIMEOUT_ULTRA_FAST = 1.5          # Reducido de 2s
TIMEOUT_FAST = 3                  # Reducido de 5s
TIMEOUT_NORMAL = 6                # Reducido de 8s
TIMEOUT_PATIENT = 10              # NUEVO: Para sitios pesados
TIMEOUT_LAST_RESORT = 15          # NUEVO: Último intento

# Cache simple para resolución de dominios
_domain_cache = {}
_cache_max_size = 100


# ---------------------------
# Utilidades locales
# ---------------------------

def _socials_from_html(html: str) -> dict:
    """Extract social networks from HTML - improved to avoid wrong URLs"""
    out = {}
    if not html:
        return out
    soup = BeautifulSoup(html, "lxml")

    # Find social links with improved filtering
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"].strip()
        if not href:
            continue
        
        href_lower = href.lower()
        
        # Skip obvious non-social pages - enhanced filtering
        if any(skip in href_lower for skip in [
            "privacy", "privacidad", "terms", "condiciones", 
            "cookies", "legal", "contact", "contacto", "notices",
            "policy", "politica", "about/legal", "support", 
            "help", "ayuda", "faq", "aviso", "disclaimer"
        ]):
            continue
            
        # Skip obviously wrong URLs (too long, weird parameters)
        if len(href) > 200 or "?" in href and len(href.split("?")[1]) > 50:
            continue
        
        # Detect social networks with better filtering
        if "linkedin.com/company" in href_lower and "linkedin" not in out:
            out["linkedin"] = href
        elif "facebook.com" in href_lower and "facebook" not in out:
            # Only valid Facebook pages
            if "/pages/" in href_lower or (href_lower.count("/") >= 3 and not any(x in href_lower for x in ["sharer", "login", "help"])):
                out["facebook"] = href
        elif ("twitter.com" in href_lower or "x.com" in href_lower) and "twitter" not in out:
            # Skip Twitter share/login links
            if not any(x in href_lower for x in ["share", "login", "oauth", "auth"]):
                out["twitter"] = href
        elif "instagram.com" in href_lower and "instagram" not in out:
            if not any(x in href_lower for x in ["share", "login", "oauth"]):
                out["instagram"] = href
        elif "youtube.com" in href_lower and "youtube" not in out:
            if any(x in href_lower for x in ["/channel/", "/c/", "/user/", "/@"]):
                out["youtube"] = href
        elif "tiktok.com" in href_lower and "tiktok" not in out:
            if not any(x in href_lower for x in ["share", "login"]):
                out["tiktok"] = href
        elif "github.com" in href_lower and "github" not in out:
            if not any(x in href_lower for x in ["login", "signup"]):
                out["github"] = href

    return out


# ---------------------------
# FastAPI
# ---------------------------

app = FastAPI(title="Maxi GTM Scan", version="0.2.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/scan", response_model=ScanResponse, summary="Escanear información de empresa")
async def scan(req: ScanRequest):
    """
    ESCÁNER ULTRA-OPTIMIZADO:
    - Timeouts escalonados inteligentes
    - Cache de domain resolution
    - Manejo robusto de errores con diagnósticos
    - Optimizado para Render y Clay
    """
    # 📊 PROFILER - Inicio del escaneo
    total_start = time.time()
    timings = {}
    error_details = []
    
    try:
        # 🎯 ETAPA 1: SMART DOMAIN RESOLUTION CON CACHE
        step_start = time.time()
        print(f"🔍 Resolviendo dominio {req.domain}")
        
        try:
            # Check cache first
            if req.domain in _domain_cache:
                base = _domain_cache[req.domain]
                print(f"✅ Cache hit para {req.domain} -> {base}")
            else:
                base = smart_domain_resolver(req.domain, timeout=2)  # Timeout aún más agresivo
                # Add to cache
                if len(_domain_cache) >= _cache_max_size:
                    # Simple LRU: remove first item
                    _domain_cache.pop(next(iter(_domain_cache)))
                _domain_cache[req.domain] = base
                
            timings["domain_resolution"] = time.time() - step_start
            print(f"✅ Dominio resuelto a {base} en {timings['domain_resolution']:.2f}s")
        except Exception as e:
            error_details.append(f"Domain resolution failed: {str(e)}")
            raise HTTPException(status_code=400, detail={
                "error": "Domain resolution failed",
                "domain": req.domain,
                "details": f"Could not resolve domain variations for {req.domain}. Check if domain is valid.",
                "suggestions": ["Verify domain spelling", "Try with/without www", "Check if domain exists"]
            })

        # 🌐 ETAPA 2: FETCH HTML CON TIMEOUTS ULTRA-OPTIMIZADOS
        step_start = time.time()
        from .fetch import extract_internal_links
        
        home_html = None
        fetch_attempts = [
            {"timeout": TIMEOUT_ULTRA_FAST, "name": "ultra-fast"},
            {"timeout": TIMEOUT_FAST, "name": "fast"}, 
            {"timeout": TIMEOUT_NORMAL, "name": "normal"},
            {"timeout": TIMEOUT_PATIENT, "name": "patient"},
            {"timeout": TIMEOUT_LAST_RESORT, "name": "last-resort"}
        ]
        
        for i, attempt in enumerate(fetch_attempts):
            try:
                print(f"⚡ Intento {i+1}: {attempt['name']} ({attempt['timeout']}s)")
                result = await fetch_many([base], respect_robots=False, timeout=attempt['timeout'])
                home_html = result[0][1] if result and result[0] else None
                
                if home_html:
                    print(f"✅ HTML obtenido en intento {i+1}")
                    break
                else:
                    error_details.append(f"Attempt {i+1} ({attempt['name']}): No HTML returned")
                    
            except Exception as e:
                error_details.append(f"Attempt {i+1} ({attempt['name']}): {str(e)}")
                continue
        
        timings["html_fetch"] = time.time() - step_start

        if not home_html:
            raise HTTPException(status_code=404, detail={
                "error": "Website not accessible",
                "domain": req.domain,
                "resolved_url": base,
                "details": f"Website did not respond after 3 attempts (2s, 5s, 8s timeouts)",
                "attempts": error_details[-3:] if len(error_details) >= 3 else error_details,
                "suggestions": [
                    "Website might be down or very slow",
                    "Try again in a few minutes", 
                    "Check if website loads in browser",
                    "Website might block automated requests"
                ]
            })
        
        print(f"✅ HTML obtenido en {timings['html_fetch']:.2f}s, tamaño: {len(home_html)}")

        # 🏢 ETAPA 3: COMPANY NAME EXTRACTION OPTIMIZADA
        step_start = time.time()
        try:
            normalized_name = normalize_company_name(req.company_name) if req.company_name else None
            company_name = extract_company_name_from_html(home_html, req.domain, fallback_name=normalized_name)
            timings["company_name"] = time.time() - step_start
            print(f"🏢 Company: '{company_name}' en {timings['company_name']:.3f}s")
        except Exception as e:
            company_name = req.domain.split('.')[0].title()  # Fallback
            error_details.append(f"Company name extraction failed: {str(e)}")
            timings["company_name"] = time.time() - step_start

        # 🏭 ETAPA 4: INDUSTRY DETECTION ULTRA-OPTIMIZADA
        step_start = time.time()
        try:
            # Solo usar contenido más relevante (título + meta + primeros 3000 chars)
            texto_optimizado = home_html[:3000].lower()
            if company_name:
                texto_optimizado += " " + company_name.lower()
            
            principal, secundaria = detectar_principal_y_secundaria(texto_optimizado, req.domain)
            timings["industry_detection"] = time.time() - step_start
            print(f"🏭 Industry: '{principal}' en {timings['industry_detection']:.3f}s")
        except Exception as e:
            principal = "No determinada"
            secundaria = None
            error_details.append(f"Industry detection failed: {str(e)}")
            print(f"❌ Industry Detection Error: {str(e)}")
            timings["industry_detection"] = time.time() - step_start

        # 💻 ETAPA 5: TECH STACK DETECTION OPTIMIZADA
        step_start = time.time()
        tech_stack = {}
        try:
            tech = detect_tech(base, home_html)
            tech_by_category = {}
            
            for tech_item in tech:
                category = tech_item.get("category", "other")
                if category not in tech_by_category:
                    tech_by_category[category] = {"tools": set(), "evidence": []}
                
                tech_by_category[category]["tools"].update(tech_item.get("tools", []))
                evidence = tech_item.get("evidence", "")
                if evidence:
                    tech_by_category[category]["evidence"].append(evidence)

            for cat, data in tech_by_category.items():
                if data["tools"]:  # Solo incluir categorías con tools
                    tech_stack[cat] = TechFingerprint(
                        tools=list(data["tools"]),
                        evidence=" | ".join(data["evidence"][:2])  # Max 2 evidencias
                    )
            
            timings["tech_stack"] = time.time() - step_start
            print(f"💻 Tech: {len(tech_stack)} categorías en {timings['tech_stack']:.3f}s")
            
        except Exception as e:
            error_details.append(f"Tech stack detection failed: {str(e)}")
            timings["tech_stack"] = time.time() - step_start

        # 🔗 ETAPA 6: PÁGINAS ADICIONALES (ULTRA-OPTIMIZADO)
        step_start = time.time()
        additional_pages = []
        social = {}
        emails = []
        news_items = []
        
        # Solo buscar páginas adicionales si el request lo permite y tenemos tiempo
        if req.max_pages > 1 and timings.get("html_fetch", 0) < 3:  # Aún más agresivo: 5→3
            try:
                # Discovery ultra-limitado
                links = extract_internal_links(base, home_html, max_links=MAX_INTERNAL_LINKS)  # Usa config
                scored = [(keyword_score(httpx.URL(u).path), u) for u in links if not looks_blocklisted(u)]
                scored.sort(reverse=True, key=lambda x: x[0])
                
                candidates = [base] + [u for _, u in scored[:TOP_CANDIDATES_BY_KEYWORD]]  # Usa config
                max_pages = min(req.max_pages, MAX_PAGES_FREE_PLAN)  # Usa config
                candidates = candidates[:max_pages]
                
                # Fetch adicional con timeout muy corto
                fetched = await fetch_many(candidates, respect_robots=req.respect_robots, timeout=TIMEOUT_FAST)  # Usa config
                
                for final_url, html in fetched:
                    if html and final_url != base:
                        additional_pages.append(final_url)
                        
                        # Extracciones ultra-limitadas para no perder tiempo
                        if len(social) < 2:
                            s = _socials_from_html(html)
                            social.update({k: v for k, v in s.items() if k not in social})
                        
                        if len(emails) < 2:  # Reducido de 3 a 2
                            page_emails = extract_emails(html)
                            emails.extend(page_emails[:1])  # Solo 1 email por página
                            
            except Exception as e:
                error_details.append(f"Additional pages processing failed: {str(e)}")
        else:
            print(f"⏩ Saltando páginas adicionales (fetch time: {timings.get('html_fetch', 0):.2f}s)")
        
        timings["additional_processing"] = time.time() - step_start

        # 📊 ETAPA 7: SEO METRICS BÁSICOS
        step_start = time.time()
        seo_metrics = None
        try:
            home_load_time = int(timings.get("html_fetch", 0) * 1000)
            seo_metrics = extract_seo_metrics(home_html, base, request_time_ms=home_load_time)
        except Exception as e:
            error_details.append(f"SEO metrics extraction failed: {str(e)}")
        timings["seo_metrics"] = time.time() - step_start

        # 📧 SOCIAL Y EMAILS DEL HOME
        try:
            home_social = _socials_from_html(home_html)
            social.update(home_social)
            
            if emails:
                unique_emails = list(set(emails))
                social["emails"] = unique_emails[:3]
        except Exception as e:
            error_details.append(f"Social/email extraction failed: {str(e)}")

        # 📊 TIMING FINAL
        timings["total_time"] = time.time() - total_start
        
        # Log del profiler
        print(f"\n📊 SCAN PROFILER para {req.domain}:")
        for key, value in timings.items():
            if key != 'total_time':
                percentage = (value/timings['total_time']*100) if timings['total_time'] > 0 else 0
                print(f"   {key}: {value:.3f}s ({percentage:.1f}%)")
        print(f"   🎯 TOTAL: {timings['total_time']:.3f}s")
        
        if error_details:
            print(f"   ⚠️ Warnings: {len(error_details)} issues encountered")

        # � ENRIQUECIMIENTO DE DATOS EXTERNO
        enrichment_data = None
        if company_name and company_name != "Unknown":
            try:
                step_start = time.time()
                enrichment_result = await get_enrichment_data(domain_of(base), company_name)
                enrichment_time = time.time() - step_start
                
                if enrichment_result and len(enrichment_result) > 1:  # Más que solo timing
                    enrichment_data = EnrichmentData(**enrichment_result)
                    sources_found = enrichment_result.get("enrichment_timing", {}).get("sources_found", 0)
                    total_time = enrichment_result.get("enrichment_timing", {}).get("total_time_ms", 0)
                    print(f"🌐 Enrichment: {sources_found} fuentes en {total_time}ms")
                    
                    # 🔄 MEJORAR INDUSTRIA CON BUSINESS INTELLIGENCE
                    if enrichment_data.business_intelligence and enrichment_data.business_intelligence.business_type:
                        business_type = enrichment_data.business_intelligence.business_type
                        confidence = enrichment_data.business_intelligence.confidence
                        
                        # Mapear business types a industrias más específicas
                        if business_type != "Unknown" and confidence == "High":
                            improved_industry = None
                            
                            if "E-commerce" in business_type:
                                improved_industry = "E-commerce y Retail"
                            elif "Technology" in business_type or "SaaS" in business_type:
                                improved_industry = "Tecnología y Software (SaaS/Cloud)"
                            elif "Media" in business_type or "Streaming" in business_type:
                                improved_industry = "Entretenimiento y Eventos"
                            elif "Hotel" in business_type:
                                improved_industry = "Hotelería y Alojamiento"
                            elif "Manufacturing" in business_type:
                                improved_industry = "Manufactura e Industria"
                            elif "Marketing" in business_type:
                                improved_industry = "Medios, Publicidad y Marketing"
                            elif "Fintech" in business_type:
                                improved_industry = "Fintech y Servicios Financieros"
                            
                            # Solo reemplazar si la industria original era genérica o None
                            if improved_industry and (not principal or principal in ["None", "No determinada"]):
                                principal = improved_industry
                                print(f"🔄 Industria mejorada con BI: '{improved_industry}' (basado en '{business_type}')")
                    
            except Exception as e:
                print(f"🌐 Enrichment error: {str(e)}")

        # �🎯 RESPUESTA OPTIMIZADA
        all_pages = [base] + additional_pages
        
        response_data = {
            "domain": domain_of(base),
            "company_name": company_name,
            "context": ContextBlock(),
            "industry": principal,
            "tech_stack": tech_stack,
            "pages_crawled": all_pages
        }
        
        # Solo agregar campos con datos útiles
        if secundaria:
            response_data["industry_secondary"] = secundaria
        if social:
            response_data["social"] = social
        if seo_metrics:
            response_data["seo_metrics"] = seo_metrics
        if enrichment_data:
            response_data["enrichment"] = enrichment_data
        
        # News removido para optimización
        response_data["recent_news"] = []

        return ScanResponse(**response_data)

    except HTTPException:
        raise  # Re-lanzar errores HTTP con detalles
    except Exception as e:
        # Error inesperado - proporcionar diagnóstico completo
        total_time = time.time() - total_start
        print(f"❌ Error crítico después de {total_time:.2f}s: {str(e)}")
        
        raise HTTPException(status_code=500, detail={
            "error": "Unexpected scan failure",
            "domain": req.domain,
            "details": str(e),
            "scan_duration": f"{total_time:.2f}s",
            "completed_stages": list(timings.keys()),
            "error_log": error_details,
            "suggestions": [
                "Try scanning again in a few minutes",
                "Check if the domain is accessible",
                "Contact support if the issue persists"
            ]
        })


