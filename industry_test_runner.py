import sys
from app.parsers.industry import detectar_principal_y_secundaria
from app.util import base_from_domain
import httpx
from bs4 import BeautifulSoup

# Lista de dominios a testear
DOMAINS = [
    "arenalsound.com",
    "energylandia.pl",
    "thermorecetas.com",
    "miin-cosmetics.com",
    "fakegodsbrand.com",
    "saigucosmetics.com",
    "basketballemotion.com",
    "unicajabaloncesto.com",
    "accioncine.es",
    "k-tuin.com",
    "mentesexpertas.com",
    "yoursclothing.es",
    "11teamsports.es",
    "yoigo.com",
    "freshlycosmetics.com",
    "madamechocolat-shop.com",
    "desenio.es",
    "killerinktattoo.de",
    "killerinktattoo.fr",
    "littletattoos.com",
    "my-furniture.com",
    "pompeiibrand.com",
    "kaftanelegance.com",
    "due-home.com",
    "um.es"
]

async def fetch_html(domain):
    url = base_from_domain(domain)
    if not url.startswith("http"):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
    except Exception as e:
        print(f"[ERROR] {domain}: {e}")
    return ""

def extract_text(html):
    soup = BeautifulSoup(html, "lxml")
    # Extraer título, descripción y texto visible
    title = soup.title.string if soup.title else ""
    desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        desc = desc_tag["content"]
    # Extraer texto visible (limitado)
    visible = " ".join([t for t in soup.stripped_strings])
    visible = visible[:2000]  # Limitar para performance
    return f"{title} {desc} {visible}"

import asyncio

async def main():
    results = []
    for domain in DOMAINS:
        html = await fetch_html(domain)
        text = extract_text(html) if html else ""
        ind1, ind2 = detectar_principal_y_secundaria(text, domain)
        results.append({
            "domain": domain,
            "principal": ind1,
            "secundaria": ind2
        })
        print(f"{domain:30} | {ind1 or '-':40} | {ind2 or '-':40}")
    print("\nResumen por industria principal:")
    from collections import Counter
    c = Counter([r["principal"] for r in results if r["principal"]])
    for k, v in c.most_common():
        print(f"{k:40} {v}")

if __name__ == "__main__":
    asyncio.run(main())
