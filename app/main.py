# app/app/main.py
from fastapi import FastAPI, HTTPException, Body
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
# Adaptive Resource Configuration
# ===========================
import os
import asyncio
from typing import Dict, Any

def get_system_resources() -> Dict[str, Any]:
    """Detecta los recursos del sistema basado en variables de entorno y límites de contenedor"""
    # Intentar detectar límites de CPU
    try:
        cpu_limit = float(os.environ.get('CPU_LIMIT', '1.0'))
    except:
        cpu_limit = 1.0
    
    # Intentar detectar límites de memoria en MB
    try:
        memory_limit = int(os.environ.get('MEMORY_LIMIT_MB', '1024'))
    except:
        memory_limit = 1024
    
    # Determinar perfil de recursos
    if cpu_limit <= 0.2 and memory_limit <= 600:
        profile = "low"  # 0.1 CPU, 512MB
        concurrent_domains = 2
        timeout_multiplier = 1.5
        batch_size = 1
    elif cpu_limit <= 0.6 and memory_limit <= 1200:
        profile = "medium"  # 0.5 CPU, 1GB
        concurrent_domains = 4
        timeout_multiplier = 1.2
        batch_size = 2
    else:
        profile = "high"  # Más recursos
        concurrent_domains = 8
        timeout_multiplier = 1.0
        batch_size = 4
    
    return {
        "profile": profile,
        "cpu_limit": cpu_limit,
        "memory_limit_mb": memory_limit,
        "concurrent_domains": concurrent_domains,
        "timeout_multiplier": timeout_multiplier,
        "batch_size": batch_size
    }

# Sistema de configuración adaptativa
SYSTEM_CONFIG = get_system_resources()
logger.info(f"Resource profile detected: {SYSTEM_CONFIG['profile']} "
           f"(CPU: {SYSTEM_CONFIG['cpu_limit']}, RAM: {SYSTEM_CONFIG['memory_limit_mb']}MB)")

# Semáforo global para controlar concurrencia
_global_semaphore = asyncio.Semaphore(SYSTEM_CONFIG["concurrent_domains"])

# Pool de clientes HTTP reutilizable
_http_clients: Dict[str, httpx.AsyncClient] = {}

async def get_http_client(domain: str) -> httpx.AsyncClient:
    """Obtiene o crea un cliente HTTP reutilizable para el dominio"""
    if domain not in _http_clients:
        _http_clients[domain] = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10 * SYSTEM_CONFIG["timeout_multiplier"],
                read=30 * SYSTEM_CONFIG["timeout_multiplier"],
                write=10 * SYSTEM_CONFIG["timeout_multiplier"],
                pool=30 * SYSTEM_CONFIG["timeout_multiplier"]
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30
            ),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    return _http_clients[domain]


# ===========================
# AUTO-BATCHING SYSTEM (para Clay y requests múltiples)
# ===========================

# Sistema de cola para auto-batching
_pending_requests: List[Dict[str, Any]] = []
_batch_timer_active = False
_batch_lock = asyncio.Lock()

# Configuración de auto-batching
AUTO_BATCH_WAIT_TIME = 0.5  # Esperar 500ms para agrupar requests
AUTO_BATCH_MAX_SIZE = 15    # Máximo 15 dominios por batch automático
AUTO_BATCH_MIN_SIZE = 2     # Mínimo 2 para hacer batch

async def _process_pending_batch():
    """Procesa el batch pendiente de requests agrupados"""
    global _pending_requests, _batch_timer_active
    
    async with _batch_lock:
        if not _pending_requests:
            _batch_timer_active = False
            return
        
        # Tomar requests pendientes
        current_requests = _pending_requests.copy()
        _pending_requests.clear()
        _batch_timer_active = False
        
        if len(current_requests) < AUTO_BATCH_MIN_SIZE:
            # Muy pocos, procesar individualmente
            for req_info in current_requests:
                try:
                    result = await _single_scan(req_info["request"])
                    req_info["future"].set_result(UnifiedScanResponse(
                        scan_type="single",
                        single_result=result
                    ))
                except Exception as e:
                    req_info["future"].set_exception(e)
        else:
            # Suficientes para batch, agrupar por dominio
            domains = [req_info["request"].domain for req_info in current_requests]
            
            try:
                # Procesar como batch
                batch_result = await _batch_scan(domains)
                
                # Distribuir resultados a cada future individual
                for req_info in current_requests:
                    domain = req_info["request"].domain
                    
                    # Buscar resultado para este dominio en el batch
                    if (batch_result.batch_result and 
                        domain in batch_result.batch_result.results):
                        
                        domain_result = batch_result.batch_result.results[domain]
                        
                        if domain_result.get("success"):
                            # Convertir resultado de batch a formato single
                            single_response = ScanResponse(
                                domain=domain,
                                company_name=domain_result.get("data", {}).get("company_name"),
                                context=ContextBlock(summary=domain_result.get("data", {}).get("context_summary")),
                                industry=domain_result.get("data", {}).get("industry"),
                                industry_secondary=domain_result.get("data", {}).get("industry_secondary"),
                                tech_stack={},
                                social={},
                                pages_crawled=[domain],
                                recent_news=[]
                            )
                            
                            req_info["future"].set_result(UnifiedScanResponse(
                                scan_type="single",
                                single_result=single_response
                            ))
                        else:
                            # Error en el dominio específico
                            req_info["future"].set_exception(
                                HTTPException(status_code=500, detail=domain_result.get("error", "Scan failed"))
                            )
                    else:
                        # Dominio no encontrado en resultados
                        req_info["future"].set_exception(
                            HTTPException(status_code=500, detail="Domain not found in batch results")
                        )
                        
            except Exception as e:
                # Error en todo el batch, fallar todos los requests
                for req_info in current_requests:
                    req_info["future"].set_exception(e)

async def _maybe_auto_batch(request: ScanRequest) -> UnifiedScanResponse:
    """Decide si agrupar el request o procesarlo inmediatamente"""
    global _pending_requests, _batch_timer_active
    
    # Solo hacer auto-batch para requests de dominio único
    if not request.domain or request.domains:
        if request.domains:
            return await _batch_scan(request.domains)
        else:
            result = await _single_scan(request)
            return UnifiedScanResponse(scan_type="single", single_result=result)
    
    async with _batch_lock:
        # Crear future para este request
        future = asyncio.Future()
        
        # Agregar a la cola
        _pending_requests.append({
            "request": request,
            "future": future,
            "timestamp": time.time()
        })
        
        # Si es el primer request o no hay timer activo, iniciar timer
        if not _batch_timer_active:
            _batch_timer_active = True
            
            # Programar procesamiento del batch
            asyncio.create_task(_wait_and_process_batch())
        
        # Si ya tenemos suficientes requests, procesar inmediatamente
        if len(_pending_requests) >= AUTO_BATCH_MAX_SIZE:
            asyncio.create_task(_process_pending_batch())
    
    # Esperar resultado
    return await future

async def _wait_and_process_batch():
    """Espera el tiempo de auto-batch y luego procesa"""
    await asyncio.sleep(AUTO_BATCH_WAIT_TIME)
    await _process_pending_batch()


# ===========================
# Config optimizada (performance final)
# ===========================
MAX_INTERNAL_LINKS = 40           # Reducido más: 60→40
TOP_CANDIDATES_BY_KEYWORD = 10    # Aumentado para DigitalOcean: 6→10
MAX_PAGES_FREE_PLAN = 15          # Aumentado para DigitalOcean: 2→15
TIMEOUT_ULTRA_FAST = int(1.5 * SYSTEM_CONFIG["timeout_multiplier"])
TIMEOUT_FAST = int(3 * SYSTEM_CONFIG["timeout_multiplier"])
TIMEOUT_NORMAL = int(6 * SYSTEM_CONFIG["timeout_multiplier"])
TIMEOUT_PATIENT = int(10 * SYSTEM_CONFIG["timeout_multiplier"])
TIMEOUT_LAST_RESORT = int(15 * SYSTEM_CONFIG["timeout_multiplier"])

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

app = FastAPI(title="GTM Scanner Pro", version="1.0.0", description="🚀 Advanced GTM Scanner with Enhanced Tech Detection")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/scan", response_model=ScanResponse, summary="Escanear información de empresa")
async def scan(req: ScanRequest):
    """
    ESCÁNER GTM OPTIMIZADO PARA CLAY:
    - Devuelve datos directamente sin wrappers
    - Detección de CRM, tech stack, industria
    - Análisis de SEO y métricas sociales
    - Optimizado para integración con Clay
    """
    
    # Procesar directamente el scan único - devolver datos planos para Clay
    result = await _single_scan(req)
    return result


async def _batch_scan(domains: List[str]) -> UnifiedScanResponse:
    """Procesa múltiples dominios en paralelo de manera optimizada"""
    if len(domains) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 domains per batch")
    
    start_time = time.time()
    
    async with _global_semaphore:
        try:
            # Usar el scanner optimizado
            from .optimized_parallel_scanner import OptimizedParallelScanner
            
            scanner = OptimizedParallelScanner(
                semaphore=_global_semaphore,
                http_clients=_http_clients,
                system_config=SYSTEM_CONFIG
            )
            
            results = await scanner.scan_multiple_domains(domains)
            
            # Estadísticas de la ejecución
            total_time = time.time() - start_time
            
            # El scanner devuelve un dict con structure diferente, necesitamos adaptarlo
            scan_results = {}
            successful_scans = 0
            
            for result in results.get("results", []):
                domain = result.get("domain")
                if result.get("status") == "success":
                    successful_scans += 1
                    scan_results[domain] = {
                        "success": True,
                        "status": "success",
                        "data": result.get("data", {}),
                        "processing_time": result.get("processing_time", 0)
                    }
                else:
                    scan_results[domain] = {
                        "success": False,
                        "status": result.get("status", "error"),
                        "error": result.get("error", "Unknown error"),
                        "processing_time": result.get("processing_time", 0)
                    }
            
            batch_response = BatchScanResponse(
                batch_id=f"batch_{int(time.time())}",
                total_domains=len(domains),
                successful_scans=successful_scans,
                failed_scans=len(domains) - successful_scans,
                execution_time=f"{total_time:.2f}s",
                resource_profile=SYSTEM_CONFIG["profile"],
                results=scan_results,
                performance_stats={
                    "avg_time_per_domain": f"{total_time / len(domains):.2f}s",
                    "success_rate": f"{(successful_scans / len(domains) * 100):.1f}%",
                    "concurrent_limit": SYSTEM_CONFIG["concurrent_domains"],
                    "memory_profile": SYSTEM_CONFIG.get("memory_limit_mb", "unknown")
                }
            )
            
            return UnifiedScanResponse(
                scan_type="batch", 
                batch_result=batch_response
            )
            
        except Exception as e:
            logger.error(f"Batch scan error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Batch scan failed: {str(e)}"
            )


async def _single_scan(req: ScanRequest) -> ScanResponse:
    """
    ESCÁNER INDIVIDUAL ULTRA-OPTIMIZADO:
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
                base = smart_domain_resolver(req.domain, timeout=2 * SYSTEM_CONFIG["timeout_multiplier"])
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

        # 💻 ETAPA 5: TECH STACK DETECTION OPTIMIZADA - MEJORADO PARA MÚLTIPLES PÁGINAS
        step_start = time.time()
        tech_stack = {}
        try:
            # Analizar tech stack de la homepage
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

            # ⚠️ NO construir tech_stack aquí - esperar a procesar todas las páginas
            
            timings["tech_stack"] = time.time() - step_start
            print(f"💻 Tech: análisis inicial en {timings['tech_stack']:.3f}s")
            
        except Exception as e:
            error_details.append(f"Tech stack detection failed: {str(e)}")
            timings["tech_stack"] = time.time() - step_start

        # 🔗 ETAPA 6: PÁGINAS ADICIONALES (ULTRA-OPTIMIZADO)
        step_start = time.time()
        additional_pages = []
        social = {}
        emails = []
        news_items = []
        
        # Solo buscar páginas adicionales si el request lo permite
        if req.max_pages > 1:  # Removemos la restricción de timeout
            try:
                # Discovery mejorado para encontrar páginas con CRM/tech
                links = extract_internal_links(base, home_html, max_links=MAX_INTERNAL_LINKS)  # Usa config
                scored = [(keyword_score(httpx.URL(u).path), u) for u in links if not looks_blocklisted(u)]
                scored.sort(reverse=True, key=lambda x: x[0])
                
                candidates = [base] + [u for _, u in scored[:TOP_CANDIDATES_BY_KEYWORD]]  # Usa config
                
                # ✅ NUEVO: Agregar extra_urls si están especificadas
                if req.extra_urls:
                    extra_urls_str = [str(url) for url in req.extra_urls]
                    candidates.extend(extra_urls_str)
                    print(f"📌 Agregadas {len(extra_urls_str)} URLs extra: {extra_urls_str}")
                
                max_pages = min(req.max_pages, MAX_PAGES_FREE_PLAN)  # Usa config
                candidates = candidates[:max_pages]
                
                print(f"🔗 Explorando {len(candidates)} páginas candidatas para {req.domain}")
                
                # Fetch adicional con timeout optimizado
                fetched = await fetch_many(candidates, respect_robots=req.respect_robots, timeout=TIMEOUT_FAST)  # Usa config
                
                for final_url, html in fetched:
                    if html and final_url != base:
                        additional_pages.append(final_url)
                        
                        # ✅ NUEVO: Analizar tech stack en páginas adicionales
                        try:
                            additional_tech = detect_tech(final_url, html)
                            for tech_item in additional_tech:
                                category = tech_item.get("category", "other")
                                if category not in tech_by_category:
                                    tech_by_category[category] = {"tools": set(), "evidence": []}
                                
                                tech_by_category[category]["tools"].update(tech_item.get("tools", []))
                                evidence = tech_item.get("evidence", "")
                                if evidence:
                                    tech_by_category[category]["evidence"].append(evidence)
                        except Exception as e:
                            print(f"⚠️ Error analyzing tech stack for {final_url}: {str(e)}")
                        
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
            print(f"⏩ Páginas adicionales deshabilitadas (max_pages={req.max_pages})")
        
        timings["additional_processing"] = time.time() - step_start

        # � CONSTRUIR TECH_STACK FINAL después de analizar todas las páginas
        try:
            for cat, data in tech_by_category.items():
                if data["tools"]:  # Solo incluir categorías con tools
                    tech_stack[cat] = TechFingerprint(
                        tools=list(data["tools"]),
                        evidence=" | ".join(data["evidence"][:2])  # Max 2 evidencias
                    )
            print(f"🔧 Tech Stack final: {len(tech_stack)} categorías")
        except Exception as e:
            error_details.append(f"Tech stack final construction failed: {str(e)}")

        # �📊 ETAPA 7: SEO METRICS BÁSICOS
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


# ===========================
# RESOURCE MONITORING ENDPOINT
# ===========================

@app.get("/system/resources")
async def get_system_status():
    """
    Endpoint para monitorear el estado del sistema y recursos
    """
    return {
        "system_config": SYSTEM_CONFIG,
        "active_connections": len(_http_clients),
        "semaphore_available": _global_semaphore._value,
        "cache_size": len(_domain_cache),
        "uptime": "running",
        "optimization_tips": [
            f"Current profile: {SYSTEM_CONFIG['profile']}",
            f"Max concurrent domains: {SYSTEM_CONFIG['concurrent_domains']}",
            f"Timeout multiplier: {SYSTEM_CONFIG['timeout_multiplier']}x",
            "Monitor memory usage with limited resources"
        ]
    }