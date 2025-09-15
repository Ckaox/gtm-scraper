#!/usr/bin/env python3
"""
Análisis específico del problema de zara.com
"""
import asyncio
import httpx

async def analyze_zara():
    """Analizar por qué zara.com obtiene poco contenido"""
    print("👗 ANÁLISIS DE ZARA.COM")
    print("=" * 50)
    
    # Test directo con diferentes user agents
    headers_list = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        {},  # Sin user agent
    ]
    
    for i, headers in enumerate(headers_list, 1):
        print(f"\n🔍 Test {i} - Headers: {headers}")
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                response = await client.get("https://zara.com", headers=headers)
                
                print(f"  Status: {response.status_code}")
                print(f"  Final URL: {response.url}")
                print(f"  HTML size: {len(response.text)} chars")
                print(f"  Headers: {dict(response.headers)}")
                
                if len(response.text) > 1000:
                    # Extraer info relevante
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    title = soup.find('title')
                    if title:
                        print(f"  Title: '{title.get_text()}'")
                    
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        print(f"  Meta desc: '{meta_desc.get('content', '')[:100]}...'")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test con el scanner actual para comparar
    print(f"\n🔍 Test con scanner actual:")
    from app.main import scan
    from app.schemas import ScanRequest
    
    request = ScanRequest(domain="zara.com")
    resultado = await scan(request)
    
    print(f"  Company: {resultado.company_name}")
    print(f"  Industry: {resultado.industry}")
    print(f"  Context: {resultado.context.summary if resultado.context else 'None'}")
    print(f"  Tech stack: {len(resultado.tech_stack) if resultado.tech_stack else 0} categories")

if __name__ == "__main__":
    asyncio.run(analyze_zara())