# app/app/parsers/industry.py
from typing import List, Dict, Tuple, Optional

# ============================================================
# DICCIONARIO DE INDUSTRIAS (títulos en español) -> keywords ES/EN
# - Mantén títulos concisos, en español
# - Keywords generosas (ES/EN), minúsculas, sin tildes no es necesario
# - Coincidimos por substring en texto normalizado a lower
# ============================================================

INDUSTRIAS: Dict[str, List[str]] = {
    # Salud y ciencias de la vida
    "Salud (Hospitales y Clínicas)": [
        "salud", "hospital", "hospitales", "clinica", "clínica", "sanatorio",
        "centro medico", "emergencias", "cuidados intensivos",
        "healthcare", "medical center", "emergency care", "icu", "er"
    ],
    "Laboratorios y Diagnóstico": [
        "laboratorio", "diagnostico", "diagnóstico", "analisis clinicos", "rayos x",
        "imaginologia", "imagenologia", "resonancia", "analítica", "hematologia",
        "laboratory", "diagnostics", "imaging", "radiology", "pathology"
    ],
    "Farmacéutica y Biotecnología": [
        "farmaceutica", "farmacéutica", "biotecnologia", "biotecnológica", "investigacion clinica",
        "ensayo clinico", "ensayos clinicos", "distribuidor farmaceutico",
        "pharma", "pharmaceutical", "biotech", "clinical trial", "cmo", "cro"
    ],
    "Telemedicina y Healthtech": [
        "telemedicina", "teleconsulta", "historia clinica electronica", "hce", "turnos online",
        "monitoreo remoto", "wearables", "salud digital",
        "telehealth", "telemedicine", "ehr", "emr", "digital health", "remote monitoring"
    ],

    # Educación
    "Educación (Escuelas y Universidades)": [
        "educacion", "educación", "escuela", "colegio", "universidad", "campus", "facultad",
        "licenciatura", "posgrado", "carrera", "instituto",
        "school", "college", "university", "campus", "faculty", "k12"
    ],
    "EdTech y e-Learning": [
        "elearning", "e-learning", "plataforma educativa", "curso online", "capacitacion online",
        "lms", "aula virtual",
        "edtech", "online course", "learning platform", "mooc", "lms", "virtual classroom"
    ],

    # Tecnología
    "Tecnología y Software (SaaS/Cloud)": [
        "tecnologia", "tecnología", "software", "saas", "paas", "iaas", "nube", "cloud",
        "microservicios", "api", "plataforma", "producto digital", "devops",
        "software as a service", "cloud computing", "platform", "product-led", "microservices"
    ],
    "Ciberseguridad": [
        "ciberseguridad", "seguridad informatica", "pentesting", "firewall", "siem", "sso",
        "gestor de identidades", "zero trust", "endpoint",
        "cybersecurity", "infosec", "xdr", "iam", "sso", "mfa", "edr"
    ],
    "IA, Datos y Analítica": [
        "inteligencia artificial", "ia", "machine learning", "aprendizaje automatico", "nlp",
        "vision por computadora", "big data", "analitica", "analítica", "datos",
        "artificial intelligence", "ml", "deep learning", "computer vision", "analytics", "data"
    ],
    "Hardware y Electrónica": [
        "hardware", "iot", "dispositivo", "electronica", "electrónica", "placa", "sensor",
        "fabricacion electronica",
        "electronics", "device", "embedded", "firmware", "pcb", "sensor", "semiconductor"
    ],
    "Cloud e Infraestructura": [
        "infraestructura", "observabilidad", "monitorizacion", "kubernetes", "contenedor",
        "cdn", "edge", "sre", "site reliability",
        "infrastructure", "observability", "monitoring", "k8s", "containers", "cdn", "edge"
    ],

    # Finanzas
    "Servicios Financieros (Banca)": [
        "banco", "banca", "finanzas", "creditos", "prestamos", "hipoteca", "cuenta corriente",
        "cajero", "pago de servicios",
        "bank", "banking", "loans", "mortgage", "checking account", "atm"
    ],
    "Fintech y Pagos": [
        "fintech", "billetera", "pagos", "psp", "adquirencia", "pos", "qr", "wallet",
        "transferencias", "open banking",
        "payments", "acquiring", "payment gateway", "wallet", "bnpl", "open banking"
    ],
    "Seguros (Insurtech)": [
        "seguros", "aseguradora", "poliza", "siniestralidad", "broker de seguros",
        "insurance", "insurtech", "policy", "underwriting", "broker"
    ],
    "Inversiones y Capital": [
        "inversiones", "cartera", "corredor de bolsa", "fondo comun", "asset management",
        "capital privado", "capital de riesgo",
        "investment", "portfolio", "brokerage", "asset management", "private equity", "venture capital"
    ],

    # Comercio y consumo
    "Comercio Electrónico (E-commerce)": [
        "ecommerce", "tienda online", "carrito", "checkout", "shopify", "woocommerce", "prestashop",
        "marketplace", "plataforma de comercio",
        "e-commerce", "online store", "cart", "marketplace", "magento", "bigcommerce"
    ],
    "Retail (Tiendas Físicas)": [
        "retail", "tienda", "sucursal", "punto de venta", "caja", "inventario", "omnichannel",
        "store", "pos", "point of sale", "inventory", "brick and mortar", "omnichannel"
    ],
    "Moda y Calzado": [
        "moda", "indumentaria", "ropa", "calzado", "textil", "boutique", "prendas",
        "fashion", "apparel", "footwear", "garment"
    ],
    "Alimentos y Bebidas (F&B)": [
        "alimentos", "bebidas", "comida", "fabrica de alimentos", "distribuidor de alimentos",
        "food", "beverage", "cpg", "food processing", "foodservice"
    ],

    # Agro y recursos
    "Agricultura y Agroindustria": [
        "agricultura", "agro", "agroindustria", "agrícola", "cultivo", "granja", "semillas",
        "agriculture", "farming", "agribusiness", "crop", "seed"
    ],
    "Ganadería y Pesca": [
        "ganaderia", "ganadería", "feedlot", "lecheria", "pesca", "acuicultura",
        "livestock", "dairy", "fishery", "aquaculture"
    ],
    "Minería y Metales": [
        "mineria", "mina", "metales", "acero", "aluminio", "cobre", "extraccion",
        "mining", "metals", "steel", "aluminum", "copper", "extraction"
    ],
    "Química y Plásticos": [
        "quimica", "química", "plastico", "plásticos", "compuesto", "polimero", "resina",
        "chemical", "plastics", "polymer", "resin"
    ],
    "Papel, Envases y Packaging": [
        "papel", "carton", "cartón", "packaging", "envase", "empaque", "impresion",
        "paper", "packaging", "carton", "printing", "label"
    ],

    # Energía y servicios públicos
    "Energía (Petróleo y Gas)": [
        "petroleo", "petróleo", "oleoducto", "gas", "refineria", "upstream", "downstream",
        "oil", "gas", "pipeline", "refinery", "upstream", "downstream"
    ],
    "Energías Renovables": [
        "energia renovable", "energias renovables", "solar", "eolica", "eólica", "fotovoltaica",
        "wind", "solar power", "pv", "renewable energy"
    ],
    "Utilities (Luz, Agua, Gas)": [
        "distribuidora electrica", "electricidad", "agua potable", "saneamiento", "gas natural",
        "utility", "electric utility", "water utility", "natural gas", "grid"
    ],

    # Construcción, inmuebles y hogar
    "Construcción e Ingeniería": [
        "construccion", "construcción", "obra", "ingenieria", "contratista", "obra civil",
        "construction", "engineering", "contractor", "civil works"
    ],
    "Inmobiliario y PropTech": [
        "inmobiliaria", "bienes raices", "bienes raíces", "alquiler", "propiedades",
        "real estate", "property", "leasing", "proptech"
    ],
    "Hogar, Muebles y Decoración": [
        "muebles", "decoracion", "hogar", "equipamiento", "electrodomesticos",
        "furniture", "home decor", "appliance", "home goods"
    ],

    # Viajes, turismo y gastronomía
    "Viajes y Turismo": [
        "turismo", "agencia de viajes", "tour", "paquete turistico", "pasajes",
        "travel", "tourism", "travel agency", "tour operator"
    ],
    "Hotelería y Alojamiento": [
        "hotel", "hostel", "alojamiento", "resort", "spa", "hospedaje",
        "hotel", "lodging", "resort", "hospitality"
    ],
    "Restaurantes y Catering": [
        "restaurante", "bar", "cafeteria", "gastronomia", "catering", "foodservice",
        "restaurant", "bar", "cafe", "catering", "food service"
    ],

    # Medios, publicidad y entretenimiento
    "Medios, Publicidad y Marketing": [
        "marketing", "publicidad", "agencia", "seo", "sem", "performance marketing",
        "prensa", "pr",
        "advertising", "media", "marketing agency", "seo", "sem"
    ],
    "Entretenimiento y Eventos": [
        "entretenimiento", "evento", "ticketing", "concierto", "festival", "teatro",
        "entertainment", "events", "ticketing", "concert", "festival"
    ],
    "Juegos y eSports": [
        "videojuegos", "gaming", "esports", "juego movil", "game studio",
        "video game", "game dev", "game studio", "mobile game"
    ],

    # Telecom y digital
    "Telecomunicaciones e ISP": [
        "telecom", "telefonia", "telefonía", "isp", "fibra optica", "redes", "antena",
        "telecommunications", "mobile operator", "internet provider", "fiber", "network"
    ],

    # Servicios profesionales y legales
    "Consultoría y Servicios Profesionales": [
        "consultoria", "consultoría", "asesoria", "asesoría", "servicios profesionales",
        "consulting", "advisory", "professional services", "outsourcing"
    ],
    "Legal y Estudios Jurídicos": [
        "abogado", "estudio juridico", "legal", "contratos", "litigio", "compliance",
        "law firm", "legal services", "attorney", "litigation", "compliance"
    ],
    "Recursos Humanos y Staffing": [
        "recursos humanos", "rrhh", "seleccion", "headhunting", "staffing", "payroll",
        "human resources", "recruiting", "headhunter", "staffing", "payroll"
    ],

    # Bienestar y belleza
    "Bienestar, Fitness y Belleza": [
        "bienestar", "fitness", "gimnasio", "spa", "estetica", "cosmetica", "cosmética",
        "wellness", "gym", "spa", "beauty", "cosmetics", "aesthetic"
    ],

    # Textil, calzado y afines (manufactura consumo)
    "Textil y Confección": [
        "textil", "tela", "confeccion", "garment", "maquila", "hilanderia",
        "textile", "garment manufacturing", "spinning", "weaving"
    ],

    # Sector público y social
    "Gobierno y Sector Público": [
        "gobierno", "municipio", "provincia", "ministerio", "secretaria", "organismo publico",
        "government", "public sector", "ministry", "municipal"
    ],
    "ONG y Sin Fines de Lucro": [
        "ong", "fundacion", "fundación", "sin fines de lucro", "asociacion civil",
        "nonprofit", "ngo", "charity", "foundation"
    ],
}

# ============================================================
# DETECCIÓN CON SCORE
# - Cuenta coincidencias de keywords por industria
# - Devuelve top_k industrias con mayor score
# - También devuelve keywords que matchearon (útil para debug)
# ============================================================

def _score_text(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    low = text.lower()
    hits = []
    score = 0
    for kw in keywords:
        if kw in low:
            score += 1
            hits.append(kw)
    return score, hits

def detectar_industrias(texto: str, top_k: int = 2, min_score: int = 1) -> List[Dict[str, object]]:
    """
    Retorna una lista (máx top_k) de dicts:
    [
      {"industria": "Salud (Hospitales y Clínicas)", "score": 4, "keywords": ["hospital", "clinica", ...]},
      ...
    ]
    Solo incluye industrias con score >= min_score.
    """
    if not texto:
        return []
    resultados = []
    for industria, kws in INDUSTRIAS.items():
        s, hits = _score_text(texto, kws)
        if s >= min_score:
            resultados.append({"industria": industria, "score": s, "keywords": hits})
    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados[:top_k]

def detectar_principal_y_secundaria(texto: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Azúcar: devuelve (principal, secundaria) o (None, None).
    """
    top = detectar_industrias(texto, top_k=2, min_score=1)
    if not top:
        return None, None
    if len(top) == 1:
        return top[0]["industria"], None
    return top[0]["industria"], top[1]["industria"]
