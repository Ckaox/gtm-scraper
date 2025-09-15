#!/usr/bin/env python3
"""
Análisis específico de clasificación de McDonald's
"""
import asyncio
import httpx
from app.parsers.industry import detectar_industrias

async def analyze_mcdonalds():
    """Analizar por qué McDonald's no se clasifica como restaurante"""
    print("🍟 ANÁLISIS DE McDONALD'S")
    print("=" * 50)
    
    # Fetch HTML de McDonald's
    async with httpx.AsyncClient() as client:
        response = await client.get("https://mcdonalds.com", timeout=10)
        html = response.text
    
    print(f"HTML fetched: {len(html)} chars")
    
    # Extraer texto relevante para análisis
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        desc = meta_desc.get('content', '')
        print(f"📋 Meta description: '{desc}'")
    
    # Título
    title = soup.find('title')
    if title:
        print(f"📋 Title: '{title.get_text()}'")
    
    # Primer párrafo
    first_p = soup.find('p')
    if first_p:
        print(f"📋 First paragraph: '{first_p.get_text()[:200]}...'")
    
    # Análisis de industrias
    full_text = html[:3000].lower() + " mcdonald's"
    print(f"\n🔍 ANÁLISIS DE INDUSTRIAS:")
    
    industrias = detectar_industrias(full_text, "mcdonalds.com", top_k=5, min_score=1)
    
    if industrias:
        print(f"Industrias detectadas ({len(industrias)}):")
        for i, ind in enumerate(industrias, 1):
            print(f"  {i}. {ind['industria']} (score: {ind['score']})")
            print(f"     Keywords: {ind['keywords'][:5]}...")
    else:
        print("❌ NO SE DETECTARON INDUSTRIAS")
    
    # Buscar keywords específicas de restaurantes
    restaurant_keywords = ['restaurant', 'restaurante', 'food', 'comida', 'menu', 'burger', 'eat', 'dining']
    found_keywords = []
    for keyword in restaurant_keywords:
        if keyword in full_text:
            found_keywords.append(keyword)
    
    print(f"\n🍽️ Restaurant keywords found: {found_keywords}")
    
    return industrias

if __name__ == "__main__":
    asyncio.run(analyze_mcdonalds())