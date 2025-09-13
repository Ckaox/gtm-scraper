# app/app/parsers/industry.py
import re
from typing import Optional

# Mapa simple de palabras -> industria
INDUSTRY_KEYWORDS = {
    "SaaS": ["saas", "b2b software", "cloud-based", "subscription software"],
    "Ecommerce": ["shopify", "woocommerce", "tienda online", "ecommerce", "carrito"],
    "Hospitality": ["reservas", "restaurante", "hotel", "reserva mesa", "booking"],
    "Fintech": ["billetera", "pagos", "psp", "fintech", "crypto", "wallet", "banking"],
    "Healthcare": ["paciente", "salud", "clínica", "turnos", "hospital"],
    "Edtech": ["aprendizaje", "educación", "curso online", "lms", "estudiante"],
    "Real Estate": ["inmobiliaria", "propiedades", "alquiler", "real estate"],
    "Travel": ["turismo", "viajes", "vuelos", "paquetes", "tour"],
    "Media": ["suscripción", "noticias", "periodismo", "medio"],
    "Logistics": ["logística", "envíos", "última milla", "fulfillment"],
}

def detect_industry(text: str) -> Optional[str]:
    if not text:
        return None
    low = text.lower()
    for name, kws in INDUSTRY_KEYWORDS.items():
        for kw in kws:
            if kw in low:
                return name
    return None
