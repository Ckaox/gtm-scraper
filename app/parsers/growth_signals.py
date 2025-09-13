# app/parsers/growth_signals.py
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def detect_growth_signals(html: str, url: str) -> Dict[str, any]:
    """
    Detecta señales de crecimiento que son oro para GTM:
    - Funding announcements
    - New office openings
    - Team expansion mentions
    - Product launches
    - Partnership announcements
    """
    if not html:
        return {}
    
    text = BeautifulSoup(html, "lxml").get_text().lower()
    signals = {}
    
    # Funding signals (súper valioso)
    funding_keywords = [
        r'series [a-z]\b', r'seed round', r'funding', r'investment', 
        r'raised \$[\d.]+[mk]', r'venture capital', r'vc funding',
        r'ronda serie [a-z]', r'financiaci[oó]n', r'inversi[oó]n'
    ]
    
    funding_mentions = []
    for pattern in funding_keywords:
        matches = re.findall(f'.{{0,50}}{pattern}.{{0,50}}', text, re.I)
        funding_mentions.extend(matches)
    
    if funding_mentions:
        signals["funding_signals"] = funding_mentions[:3]  # Top 3
    
    # Growth keywords
    growth_patterns = [
        r'new office', r'expanding to', r'hiring.{0,20}people',
        r'team.{0,10}grow', r'scale.{0,10}operation',
        r'nueva oficina', r'expansion', r'contratando',
        r'crecimiento', r'escalando'
    ]
    
    growth_mentions = []
    for pattern in growth_patterns:
        matches = re.findall(f'.{{0,50}}{pattern}.{{0,50}}', text, re.I)
        growth_mentions.extend(matches)
    
    if growth_mentions:
        signals["growth_mentions"] = growth_mentions[:3]
    
    # Partnership signals
    partnership_patterns = [
        r'partnership with', r'strategic alliance', r'collaboration',
        r'integration with', r'partner.{0,20}announce',
        r'alianza con', r'colaboraci[oó]n', r'integraci[oó]n'
    ]
    
    partnership_mentions = []
    for pattern in partnership_patterns:
        matches = re.findall(f'.{{0,50}}{pattern}.{{0,50}}', text, re.I)
        partnership_mentions.extend(matches)
    
    if partnership_mentions:
        signals["partnership_signals"] = partnership_mentions[:2]
    
    # Product launch signals
    launch_patterns = [
        r'launch', r'introducing', r'new product', r'new feature',
        r'beta', r'coming soon', r'lanzamiento', r'nuevo producto'
    ]
    
    launch_mentions = []
    for pattern in launch_patterns:
        matches = re.findall(f'.{{0,50}}{pattern}.{{0,50}}', text, re.I)
        launch_mentions.extend(matches)
    
    if launch_mentions:
        signals["product_launches"] = launch_mentions[:3]
    
    return signals

def detect_urgency_indicators(html: str) -> Dict[str, any]:
    """
    Detecta indicadores de urgencia/timing que son críticos para outbound:
    - Job postings indicating rapid hiring
    - "Now hiring" language
    - Time-sensitive content
    """
    if not html:
        return {}
    
    text = BeautifulSoup(html, "lxml").get_text().lower()
    indicators = {}
    
    # Urgency keywords
    urgency_patterns = [
        r'urgent.{0,20}hire', r'immediate.{0,20}start', r'asap',
        r'rapid.{0,20}growth', r'aggressive.{0,20}expansion',
        r'urgente', r'inmediato', r'r[aá]pido crecimiento'
    ]
    
    urgency_mentions = []
    for pattern in urgency_patterns:
        matches = re.findall(f'.{{0,30}}{pattern}.{{0,30}}', text, re.I)
        urgency_mentions.extend(matches)
    
    if urgency_mentions:
        indicators["urgency_signals"] = urgency_mentions[:2]
    
    # Multiple job postings (indicates growth)
    job_count = len(re.findall(r'(developer|engineer|sales|marketing|manager)', text, re.I))
    if job_count >= 5:
        indicators["high_hiring_volume"] = f"~{job_count} job-related mentions found"
    
    return indicators

def calculate_growth_score(signals: Dict, urgency: Dict, employee_count: Optional[int] = None) -> Dict[str, any]:
    """
    Calcula un score de crecimiento que ayuda a priorizar prospects.
    """
    score = 0.0
    factors = []
    
    # Funding signals (highest value)
    if signals.get("funding_signals"):
        score += 0.4
        factors.append("Recent funding activity")
    
    # Growth mentions
    if signals.get("growth_mentions"):
        score += 0.2
        factors.append("Growth indicators mentioned")
    
    # Partnership signals
    if signals.get("partnership_signals"):
        score += 0.15
        factors.append("Strategic partnerships")
    
    # Product launches
    if signals.get("product_launches"):
        score += 0.1
        factors.append("Product innovation")
    
    # Urgency indicators
    if urgency.get("urgency_signals"):
        score += 0.1
        factors.append("Urgency indicators")
    
    # High hiring volume
    if urgency.get("high_hiring_volume"):
        score += 0.05
        factors.append("High hiring activity")
    
    # Employee count factor (smaller companies often more agile)
    if employee_count:
        if 10 <= employee_count <= 500:  # Sweet spot for many SaaS tools
            score += 0.05
            factors.append("Optimal company size")
    
    return {
        "growth_score": round(min(1.0, score), 2),
        "score_factors": factors,
        "priority_level": "High" if score >= 0.6 else "Medium" if score >= 0.3 else "Low"
    }