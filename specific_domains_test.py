#!/usr/bin/env python3
"""
Test específico para 8 dominios solicitados
"""

import asyncio
import httpx
from app.main import scan
from app.schemas import ScanRequest
from app.parsers.industry import detectar_industrias

DOMINIOS_TEST = [
    "jeep.com",
    "natosywaor.com", 
    "tiendaprado.com",
    "hawkersco.com",
    "aboutyou.es",
    "prodirectsport.es",
    "underarmour.es",
    "dia.es",
    "mango.com",  # Mango - Alternative to zara.com
    "mcdonalds.com"
]

async def test_dominio_completo(domain: str):
    """Test completo de un dominio con TODOS los campos de output"""
    print(f"\n{'='*60}")
    print(f"TESTING: {domain}")
    print(f"{'='*60}")
    
    try:
        # Crear request y escanear
        request = ScanRequest(domain=domain)
        resultado = await scan(request)
        
        # ================================================================
        # ANÁLISIS DETALLADO DE TODOS LOS OUTPUTS
        # ================================================================
        
        print(f"🌐 DOMAIN: {domain}")
        print(f"📊 PÁGINAS ESCANEADAS: {len(resultado.pages_crawled) if resultado.pages_crawled else 0}")
        
        # 1. COMPANY NAME
        print(f"\n--- 🏢 COMPANY NAME ---")
        if resultado.company_name:
            print(f"✅ Company: '{resultado.company_name}'")
        else:
            print(f"❌ Company: No detectado")
        
        # 2. INDUSTRY (Principal y Secundaria)
        print(f"\n--- 🏭 INDUSTRY ---")
        if resultado.industry:
            print(f"✅ Primary: {resultado.industry}")
        else:
            print(f"❌ Primary: No detectado")
            
        if hasattr(resultado, 'industry_secondary') and resultado.industry_secondary:
            print(f"✅ Secondary: {resultado.industry_secondary}")
        else:
            print(f"❌ Secondary: No detectado")
        
        # 3. CONTEXT (resumen y detalles)
        print(f"\n--- 📝 CONTEXT ---")
        if resultado.context:
            if resultado.context.summary:
                print(f"✅ Summary: {resultado.context.summary[:200]}...")
            else:
                print(f"❌ Summary: Vacío")
                
            if hasattr(resultado.context, 'keywords') and resultado.context.keywords:
                print(f"✅ Keywords: {resultado.context.keywords[:5]}...")
            else:
                print(f"❌ Keywords: No detectadas")
                
            if hasattr(resultado.context, 'description') and resultado.context.description:
                print(f"✅ Description: {resultado.context.description[:150]}...")
            else:
                print(f"❌ Description: No detectada")
        else:
            print(f"❌ Context: Completamente vacío")
        
        # 4. TECH STACK
        print(f"\n--- 💻 TECH STACK ---")
        if resultado.tech_stack:
            print(f"✅ Categorías detectadas: {len(resultado.tech_stack)}")
            for categoria, tech in resultado.tech_stack.items():
                tools_count = len(tech.tools) if hasattr(tech, 'tools') and tech.tools else 0
                print(f"    {categoria}: {tools_count} herramientas")
                if tools_count > 0:
                    print(f"      → {tech.tools[:3]}...")
        else:
            print(f"❌ Tech Stack: No detectado")
        
        # 5. SOCIAL MEDIA
        print(f"\n--- 📱 SOCIAL MEDIA ---")
        social = getattr(resultado, 'social', None)
        if social:
            print(f"✅ Redes detectadas: {len(social)}")
            for red, url in social.items():
                if red == 'emails':
                    print(f"    📧 {red}: {len(url)} emails" if isinstance(url, list) else f"    📧 {red}: {url}")
                else:
                    print(f"    🔗 {red}: {url[:50]}..." if len(str(url)) > 50 else f"    🔗 {red}: {url}")
        else:
            print(f"❌ Social Media: No detectado")
        
        # 6. SEO METRICS
        print(f"\n--- 🔍 SEO METRICS ---")
        seo = getattr(resultado, 'seo_metrics', None)
        if seo:
            print(f"✅ SEO Metrics disponibles:")
            for campo, valor in seo.__dict__.items() if hasattr(seo, '__dict__') else []:
                if valor:
                    print(f"    {campo}: {valor}")
                else:
                    print(f"    {campo}: No disponible")
        else:
            print(f"❌ SEO Metrics: No disponibles")
        
        # 7. ENRICHMENT DATA
        print(f"\n--- 🌟 ENRICHMENT ---")
        enrichment = getattr(resultado, 'enrichment', None)
        if enrichment:
            print(f"✅ Enrichment disponible:")
            for campo, valor in enrichment.__dict__.items() if hasattr(enrichment, '__dict__') else []:
                if valor:
                    valor_str = str(valor)[:100] + "..." if len(str(valor)) > 100 else str(valor)
                    print(f"    {campo}: {valor_str}")
        else:
            print(f"❌ Enrichment: No disponible")
        
        # 8. NEWS
        print(f"\n--- 📰 NEWS ---")
        news = getattr(resultado, 'recent_news', [])
        if news:
            print(f"✅ Noticias: {len(news)} encontradas")
            for i, noticia in enumerate(news[:3], 1):
                title = getattr(noticia, 'title', 'Sin título')[:50] + "..."
                print(f"    {i}. {title}")
        else:
            print(f"❌ News: No disponibles")
        
        # ================================================================
        # ANÁLISIS ESPECÍFICO DE INDUSTRY CON KEYWORDS
        # ================================================================
        print(f"\n--- 🔬 ANÁLISIS DETALLADO DE INDUSTRIA ---")
        full_text = ''
        if resultado.context and resultado.context.summary:
            full_text += resultado.context.summary + ' '
        if resultado.company_name:
            full_text += resultado.company_name
            
        if full_text.strip():
            industrias_detectadas = detectar_industrias(full_text, domain, top_k=5, min_score=1)
            
            if industrias_detectadas:
                print(f"✅ Industrias detectadas ({len(industrias_detectadas)}):")
                for i, ind in enumerate(industrias_detectadas, 1):
                    print(f"  {i}. {ind['industria']} (score: {ind['score']})")
                    print(f"     Keywords: {ind['keywords'][:5]}...")
            else:
                print("❌ NO SE DETECTARON INDUSTRIAS")
                print("   Texto analizado:", full_text[:100] + "..." if len(full_text) > 100 else full_text)
        else:
            print("❌ NO HAY TEXTO PARA ANALIZAR")
        
        # ================================================================
        # COMPLETITUD GENERAL
        # ================================================================
        print(f"\n--- ✅ COMPLETITUD DE DATOS ---")
        campos_completos = []
        campos_vacios = []
        campos_parciales = []
        
        # Evaluar cada campo
        if resultado.company_name:
            campos_completos.append('company_name')
        else:
            campos_vacios.append('company_name')
            
        if resultado.industry:
            campos_completos.append('industry')
        else:
            campos_vacios.append('industry')
            
        if resultado.context and resultado.context.summary:
            campos_completos.append('context_summary')
        else:
            campos_vacios.append('context_summary')
            
        if resultado.tech_stack:
            campos_completos.append('tech_stack')
        else:
            campos_vacios.append('tech_stack')
            
        social = getattr(resultado, 'social', None)
        if social:
            campos_completos.append('social_media')
        else:
            campos_vacios.append('social_media')
            
        seo = getattr(resultado, 'seo_metrics', None)
        if seo:
            campos_completos.append('seo_metrics')
        else:
            campos_vacios.append('seo_metrics')
            
        enrichment = getattr(resultado, 'enrichment', None)
        if enrichment:
            campos_completos.append('enrichment')
        else:
            campos_vacios.append('enrichment')
        
        print(f"✅ Campos completos ({len(campos_completos)}): {', '.join(campos_completos)}")
        if campos_vacios:
            print(f"❌ Campos vacíos ({len(campos_vacios)}): {', '.join(campos_vacios)}")
        if campos_parciales:
            print(f"⚠️  Campos parciales ({len(campos_parciales)}): {', '.join(campos_parciales)}")
            
        completitud = len(campos_completos) / (len(campos_completos) + len(campos_vacios)) * 100
        print(f"📊 COMPLETITUD TOTAL: {completitud:.1f}%")
            
        return resultado
        
    except Exception as e:
        print(f"❌ ERROR procesando {domain}: {str(e)}")
        return None

async def main():
    print("INICIO DEL TEST DE 8 DOMINIOS ESPECÍFICOS")
    print("=========================================\n")
    
    resultados = {}
    
    for domain in DOMINIOS_TEST:
        resultado = await test_dominio_completo(domain)
        resultados[domain] = resultado
        
        # Pequeña pausa entre requests
        await asyncio.sleep(2)
    
    # Resumen final
    print(f"\n\n{'='*80}")
    print("RESUMEN FINAL")
    print(f"{'='*80}")
    
    clasificados = 0
    no_clasificados = []
    
    for domain, resultado in resultados.items():
        if resultado and resultado.industry:
            clasificados += 1
            print(f"✅ {domain:25} → {resultado.industry}")
        else:
            no_clasificados.append(domain)
            print(f"❌ {domain:25} → NO CLASIFICADO")
    
    print(f"\nESTADÍSTICAS:")
    print(f"Clasificados: {clasificados}/{len(DOMINIOS_TEST)} ({clasificados/len(DOMINIOS_TEST)*100:.1f}%)")
    print(f"No clasificados: {len(no_clasificados)}")
    
    if no_clasificados:
        print(f"\nDOMINIOS SIN CLASIFICAR:")
        for domain in no_clasificados:
            print(f"- {domain}")
        
        print(f"\nSOLUCIONES RECOMENDADAS:")
        print("1. Expandir keywords en industrias específicas")
        print("2. Mejorar extracción de contenido web")
        print("3. Reducir score mínimo temporalmente") 
        print("4. Añadir reglas específicas por dominio")

if __name__ == "__main__":
    asyncio.run(main())
