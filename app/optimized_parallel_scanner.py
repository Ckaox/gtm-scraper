#!/usr/bin/env python3
"""
Sistema de scanning paralelo optimizado para recursos limitados
"""
import asyncio
import time
import httpx
from typing import List, Dict, Any
from .schemas import ScanRequest, ScanResponse

class OptimizedParallelScanner:
    """Scanner paralelo optimizado para recursos limitados"""
    
    def __init__(self, semaphore, http_clients, system_config):
        self.semaphore = semaphore
        self.http_clients = http_clients
        self.config = system_config
        self.processed_domains = []
        self.failed_domains = []
        
    async def scan_domain_lightweight(self, domain: str) -> Dict[str, Any]:
        """Scan ultra-ligero para múltiples dominios"""
        async with self.semaphore:  # Control de concurrencia
            start_time = time.time()
            result = {
                "domain": domain,
                "status": "success",
                "processing_time": 0,
                "data": {}
            }
            
            try:
                print(f"🔍 Scanning {domain}...")
                
                # Obtener cliente HTTP para el dominio
                if domain not in self.http_clients:
                    self.http_clients[domain] = httpx.AsyncClient(
                        timeout=httpx.Timeout(
                            connect=10 * self.config["timeout_multiplier"],
                            read=30 * self.config["timeout_multiplier"],
                            write=10 * self.config["timeout_multiplier"],
                            pool=30 * self.config["timeout_multiplier"]
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
                
                client = self.http_clients[domain]
                
                # Fetch básico con timeout optimizado
                response = await client.get(
                    f"https://{domain}",
                    timeout=5 * self.config["timeout_multiplier"]
                )
                
                html = response.text
                html_size = len(html)
                
                # Extracciones mínimas pero esenciales
                from .parsers.company_name import extract_company_name_from_html
                from .parsers.context_summary import extract_context_summary
                from .parsers.industry import detectar_principal_y_secundaria
                
                # Company name (rápido)
                company_name = extract_company_name_from_html(html, domain)
                
                # Context summary (rápido)
                context_summary = extract_context_summary(html, company_name, max_length=150)
                
                # Industry classification (ultra-rápido)
                if context_summary:
                    texto_optimizado = context_summary.lower()
                    if company_name:
                        texto_optimizado += " " + company_name.lower()
                else:
                    texto_optimizado = html[:1500].lower()  # Más conservador
                    if company_name:
                        texto_optimizado += " " + company_name.lower()
                
                principal, secundaria = detectar_principal_y_secundaria(texto_optimizado, domain)
                
                # Resultado optimizado
                result["data"] = {
                    "company_name": company_name,
                    "industry": principal,
                    "industry_secondary": secundaria,
                    "context_summary": context_summary,
                    "html_size": html_size,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
                
                result["processing_time"] = time.time() - start_time
                print(f"✅ {domain} completed in {result['processing_time']:.2f}s")
                
                return result
                
            except asyncio.TimeoutError:
                result["status"] = "timeout"
                result["error"] = f"Timeout after {self.config['timeout_ultra_fast']}s"
                print(f"⏰ {domain} timeout")
                return result
                
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
                result["processing_time"] = time.time() - start_time
                print(f"❌ {domain} error: {str(e)}")
                return result
    
    async def scan_multiple_domains(self, domains: List[str], max_concurrent: int = None) -> Dict[str, Any]:
        """Scan múltiples dominios en paralelo con control de recursos"""
        if max_concurrent is None:
            max_concurrent = self.config["max_concurrent_domains"]
        
        start_time = time.time()
        print(f"🚀 PARALLEL SCAN: {len(domains)} dominios con max {max_concurrent} concurrentes")
        print(f"   Memoria profile: {self.config['memory_profile']} ({self.config['memory_mb']}MB)")
        
        # Procesar en batches para controlar memoria
        results = []
        batch_size = max_concurrent
        
        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(domains) + batch_size - 1) // batch_size
            
            print(f"\n📦 Batch {batch_num}/{total_batches}: {len(batch)} dominios")
            
            # Procesar batch en paralelo
            batch_tasks = [self.scan_domain_lightweight(domain) for domain in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Procesar resultados del batch
            for domain, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "domain": domain,
                        "status": "exception",
                        "error": str(result),
                        "processing_time": 0
                    })
                else:
                    results.append(result)
            
            # Breve pausa entre batches para liberar memoria
            if i + batch_size < len(domains):
                await asyncio.sleep(0.1)
        
        # Estadísticas finales
        total_time = time.time() - start_time
        successful = [r for r in results if r["status"] == "success"]
        timeouts = [r for r in results if r["status"] == "timeout"]
        errors = [r for r in results if r["status"] in ["error", "exception"]]
        
        avg_processing_time = sum(r["processing_time"] for r in results) / len(results) if results else 0
        domains_per_minute = (len(domains) / total_time) * 60 if total_time > 0 else 0
        
        summary = {
            "total_domains": len(domains),
            "successful": len(successful),
            "timeouts": len(timeouts),
            "errors": len(errors),
            "success_rate": (len(successful) / len(domains)) * 100 if domains else 0,
            "total_time": total_time,
            "avg_processing_time": avg_processing_time,
            "domains_per_minute": domains_per_minute,
            "memory_profile": self.config["memory_profile"],
            "max_concurrent": max_concurrent,
            "results": results
        }
        
        print(f"\n📊 RESULTADOS DEL SCAN PARALELO:")
        print(f"   ✅ Exitosos: {len(successful)}/{len(domains)} ({summary['success_rate']:.1f}%)")
        print(f"   ⏰ Timeouts: {len(timeouts)}")
        print(f"   ❌ Errores: {len(errors)}")
        print(f"   🚀 Velocidad: {domains_per_minute:.1f} dominios/minuto")
        print(f"   ⏱️ Tiempo total: {total_time:.2f}s")
        
        return summary

async def main():
    """Test del scanner paralelo optimizado"""
    scanner = OptimizedParallelScanner()
    
    # Test con dominios conocidos
    test_domains = [
        "jeep.com",
        "natosywaor.com",
        "mango.com",
        "mcdonalds.com",
        "dia.es"
    ]
    
    print("🧪 TESTING OPTIMIZED PARALLEL SCANNER")
    print("=" * 60)
    
    results = await scanner.scan_multiple_domains(test_domains)
    
    # Mostrar algunos resultados detallados
    print(f"\n📋 DETALLES DE RESULTADOS:")
    for result in results["results"][:3]:  # Primeros 3
        if result["status"] == "success" and result.get("data"):
            data = result["data"]
            print(f"   {result['domain']}:")
            print(f"     Company: {data.get('company_name', 'N/A')}")
            print(f"     Industry: {data.get('industry', 'N/A')}")
            print(f"     Time: {result['processing_time']:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())