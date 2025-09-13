# app/app/parsers/emails.py
import re
from typing import List

MAILTO_RE = re.compile(r'href=["\']mailto:([^"\']+)["\']', re.I)
PLAIN_RE  = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)

# Filtrar “basura” común
BLACKLIST_DOMAINS = {"example.com", "email.com", "test.com"}
BLACKLIST_LOCAL = {"example", "test"}

def extract_emails(html: str) -> List[str]:
    if not html:
        return []
    
    # Limitar HTML para performance
    if len(html) > 300_000:  # 300KB max
        html = html[:300_000]
    
    out = set()

    for m in MAILTO_RE.findall(html):
        out.add(m.strip())

    for m in PLAIN_RE.findall(html):
        out.add(m.strip())

    cleaned = []
    for e in out:
        local, _, domain = e.partition("@")
        if not local or not domain:
            continue
        if domain.lower() in BLACKLIST_DOMAINS:
            continue
        if local.lower() in BLACKLIST_LOCAL:
            continue
        cleaned.append(e)
        # Límite para evitar spam
        if len(cleaned) >= 10:
            break
    
    return sorted(set(cleaned))
