#!/usr/bin/env python3
"""
Scraper paralelo para procesar múltiples dominios simultáneamente
"""

import asyncio
import time
from typing import List, Dict, Any
from app.main import scan
from app.schemas import ScanRequest, ScanResponse


class ParallelScraper:
    """Scraper que procesa múltiples dominios en paralelo"""
    
    def __init__(self, max_concurrent: int = 5, delay_between_batches: float = 1.0):
        self.max_concurrent = max_concurrent
        self.delay_between_batches = delay_between_batches
        
    async def scan_domain(self, domain: str) -> Dict[str, Any]:
        """Escanea un dominio individual"""
        try:
            print(f"🔄 Iniciando escaneo de {domain}")
            request = ScanRequest(domain=domain)
            start_time = time.time()
            
            result = await scan(request)
            
            elapsed = time.time() - start_time
            print(f"✅ {domain} completado en {elapsed:.2f}s")
            
            return {
                "domain": domain,
                "success": True,
                "result": result,
                "scan_time": elapsed,
                "error": None
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {domain} falló en {elapsed:.2f}s: {str(e)}")
            
            return {
                "domain": domain,
                "success": False,
                "result": None,
                "scan_time": elapsed,
                "error": str(e)
            }
    
    async def scan_batch(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Escanea un lote de dominios en paralelo"""
        print(f"🚀 Procesando lote de {len(domains)} dominios en paralelo (max: {self.max_concurrent})")
        
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def limited_scan(domain: str):
            async with semaphore:
                return await self.scan_domain(domain)
        
        # Ejecutar todos los escaneos en paralelo
        tasks = [limited_scan(domain) for domain in domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados y excepciones
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "domain": domains[i],
                    "success": False,
                    "result": None,
                    "scan_time": 0,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def scan_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Escanea una lista de dominios con paralelización inteligente"""
        total_start = time.time()
        all_results = []
        
        # Dividir en lotes si hay muchos dominios
        batch_size = max(self.max_concurrent, 10)  # Mínimo 10 por lote
        batches = [domains[i:i + batch_size] for i in range(0, len(domains), batch_size)]
        
        print(f"📊 Procesando {len(domains)} dominios en {len(batches)} lote(s)")
        print(f"⚙️  Configuración: max_concurrent={self.max_concurrent}, delay={self.delay_between_batches}s")
        
        for i, batch in enumerate(batches, 1):
            print(f"\n--- LOTE {i}/{len(batches)} ({len(batch)} dominios) ---")
            
            batch_results = await self.scan_batch(batch)
            all_results.extend(batch_results)
            
            # Pausa entre lotes (excepto el último)
            if i < len(batches) and self.delay_between_batches > 0:
                print(f"⏳ Pausa de {self.delay_between_batches}s entre lotes...")
                await asyncio.sleep(self.delay_between_batches)
        
        # Calcular estadísticas
        total_time = time.time() - total_start
        successful = [r for r in all_results if r["success"]]
        failed = [r for r in all_results if not r["success"]]
        
        avg_time = sum(r["scan_time"] for r in successful) / len(successful) if successful else 0
        
        stats = {
            "total_domains": len(domains),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(domains) * 100 if domains else 0,
            "total_time": total_time,
            "average_scan_time": avg_time,
            "domains_per_minute": len(domains) / (total_time / 60) if total_time > 0 else 0
        }
        
        return {
            "results": all_results,
            "stats": stats,
            "successful_results": successful,
            "failed_results": failed
        }
    
    def print_summary(self, scan_data: Dict[str, Any]):
        """Imprime un resumen de los resultados"""
        stats = scan_data["stats"]
        successful = scan_data["successful_results"]
        failed = scan_data["failed_results"]
        
        print(f"\n{'='*80}")
        print("RESUMEN DE ESCANEO PARALELO")
        print(f"{'='*80}")
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   Total dominios: {stats['total_domains']}")
        print(f"   Exitosos: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"   Fallidos: {stats['failed']}")
        print(f"   Tiempo total: {stats['total_time']:.2f}s")
        print(f"   Tiempo promedio por dominio: {stats['average_scan_time']:.2f}s")
        print(f"   Velocidad: {stats['domains_per_minute']:.1f} dominios/minuto")
        
        print(f"\n✅ DOMINIOS EXITOSOS:")
        for result in successful:
            r = result["result"]
            industry = r.industry or "Sin clasificar"
            print(f"   {result['domain']:25} → {industry}")
        
        if failed:
            print(f"\n❌ DOMINIOS FALLIDOS:")
            for result in failed:
                print(f"   {result['domain']:25} → {result['error'][:50]}...")


async def main():
    """Función principal para testing"""
    
    # Dominios de prueba
    test_domains = [
        "jeep.com",
        "natosywaor.com", 
        "tiendaprado.com",
        "hawkersco.com",
        "aboutyou.es",
        "underarmour.es",
        "dia.es"
    ]
    
    # Crear scraper paralelo
    scraper = ParallelScraper(max_concurrent=3, delay_between_batches=1.0)
    
    # Ejecutar escaneo paralelo
    print("🚀 INICIANDO ESCANEO PARALELO")
    print("=" * 50)
    
    scan_data = await scraper.scan_domains(test_domains)
    
    # Mostrar resumen
    scraper.print_summary(scan_data)
    
    return scan_data


if __name__ == "__main__":
    # Ejecutar el test paralelo
    results = asyncio.run(main())