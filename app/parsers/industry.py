# app/parsers/industry.py
from typing import List, Dict, Tuple, Optional

# ============================================================
# DICCIONARIO DE INDUSTRIAS (títulos en español) -> keywords ES/EN
# - Mantén títulos concisos, en español
# - Keywords generosas (ES/EN), minúsculas, sin tildes no es necesario
# - Coincidimos por substring en texto normalizado a lower
# ============================================================

INDUSTRIAS: Dict[str, List[str]] = {
    # Automóviles y Vehículos (NUEVA INDUSTRIA) - Reducido para evitar falsos positivos
    "Automóviles y Vehículos": [
        "automovil", "automóvil", "automoviles", "automóviles", "vehiculo comercial", "vehículo comercial", "vehiculos comerciales", "vehículos comerciales", 
        "concesionario", "concesionarios", "dealer", "dealers", "jeep", "ford", "chevrolet", "toyota", "honda", "nissan", "hyundai", "kia", "volkswagen", "bmw", "mercedes", "audi", "peugeot", "renault", "citroen", "citroën", "fiat", "seat", "skoda", "suzuki", "mazda", "mitsubishi", "subaru", "volvo", "jaguar", "land rover", "porsche", "ferrari", "lamborghini", "maserati", "tesla", "pickup", "suv", "sedan", "hatchback", "convertible", "coupe", "minivan", "truck automotriz", "camion automotriz", "camión automotriz", "motocicleta", "moto comercial", "motorcycle dealer", "scooter dealer", "atv", "quad", "repuestos automotriz", "refacciones automotriz", "auto parts", "spare parts automotriz", "taller mecanico", "taller mecánico", "mecanico automotriz", "mecánico automotriz", "mechanic shop", "garage automotriz", "servicio automotriz", "automotive service", "cambio de aceite", "oil change", "neumatico automotriz", "neumático automotriz", "tire shop", "tires dealer", "llanta automotriz", "llantas automotriz", "frenos automotriz", "brakes automotriz", "bateria automotriz", "batería automotriz", "battery automotriz", "motor automotriz", "engine automotriz", "transmision automotriz", "transmisión automotriz", "transmission automotriz", "automotive dealer", "automotive sales", "car dealership", "vehicle sales", "automotive industry"
    ],
    
    # Supermercados y Retail Alimentario (NUEVA INDUSTRIA)
    "Supermercados y Retail Alimentario": [
        "supermercado", "supermercados", "supermarket", "supermarkets", "hipermercado", "hipermercados", "hypermarket", "grocery", "groceries", "alimentacion", "alimentación", "comestibles", "fresh", "fresco", "frescos", "productos frescos", "fresh products", "mercado", "market", "marketplace alimentario", "retail alimentario", "food retail", "cadena alimentaria", "food chain", "distribucion alimentaria", "distribución alimentaria", "food distribution", "almacen", "almacén", "warehouse", "logistica alimentaria", "logística alimentaria", "food logistics", "dia", "mercadona", "carrefour", "alcampo", "lidl", "aldi", "eroski", "corte ingles", "el corte inglés", "caprabo", "consum", "simply", "mas", "más", "condis", "gadis", "froiz", "ahorramas", "ahorramás", "bonpreu", "sorli", "cash", "makro", "costco", "walmart", "kroger", "safeway", "whole foods", "trader joe", "iga", "metro", "tesco", "asda", "sainsbury", "morrisons", "fresh market", "organic market", "bio market", "eco market", "health food", "natural food", "productos organicos", "productos orgánicos", "organic products", "bio productos", "eco productos", "productos bio", "productos eco", "fresh food", "comida fresca", "alimentacion saludable", "alimentación saludable", "healthy food", "productos saludables", "healthy products"
    ],

    # Consumo, Moda y Lifestyle (agrupado)
    "Consumo, Moda y Lifestyle": [
        "retail", "tienda", "tiendas", "store", "stores", "boutique", "fashion", "apparel", "clothing", "ropa", "moda", "indumentaria", "vestimenta", "calzado", "zapatos", "zapatillas", "textil", "textiles", "prenda", "prendas", "diseño de moda", "diseñador", "diseñadora", "confeccion", "confección", "coleccion", "colección", "tendencia", "tendencias", "marca de ropa", "atelier", "sastre", "sastreria", "sastrería", "footwear", "garment", "clothing brand", "runway", "fashion show", "trendy", "style", "wardrobe", "lifestyle", "decoracion", "decoración", "hogar", "furniture", "muebles", "mueble", "home decor", "appliance", "home goods", "interior design", "home improvement", "kitchen", "bathroom", "bedroom", "living room", "lighting", "home furnishing", "home accessories", "beauty", "belleza", "cosmetica", "cosmética", "cosmeticos", "cosméticos", "cuidado personal", "skincare", "peluqueria", "peluquería", "salon de belleza", "salón de belleza", "spa", "spas", "estetica", "estética", "wellness", "fitness", "gimnasio", "gimnasios", "gym", "personal care", "personal care products", "beauty products", "beauty salon", "beauty treatment", "cosmetics", "aesthetic", "health club", "beauty industry", "makeup", "maquillaje", "perfume", "fragancia", "fragrance", "cosmetics shop", "cosmetics store", "beauty shop", "beauty store", "perfume shop", "perfume store", "skincare shop", "skincare store", "maquillaje shop", "maquillaje store", "cosmética shop", "cosmética store", "cosmetica shop", "cosmetica store", "fashion shop", "fashion store", "lifestyle shop", "lifestyle store", "ropa shop", "ropa store", "zapatos shop", "zapatos store", "calzado shop", "calzado store", "boutique shop", "boutique store", "moda shop", "moda store", "indumentaria shop", "indumentaria store", "vestimenta shop", "vestimenta store"
    ],
    # E-commerce y Tiendas Online (nuevo)
    "E-commerce y Tiendas Online": [
        "ecommerce", "e-commerce", "comercio electronico", "comercio electrónico", "tienda online", "tiendas online", "online store", "online shopping", "shop", "checkout", "carrito", "cart", "shopify", "woocommerce", "prestashop", "magento", "bigcommerce", "marketplace", "marketplaces", "venta online", "ventas online", "catalogo online", "catálogo online", "dropshipping", "fulfillment", "logistica ecommerce", "logística ecommerce", "pago online", "e-commerce platform", "online marketplace", "digital storefront", "digital commerce", "online retail", "e-shop", "eshop", "tienda virtual", "plataforma de comercio", "e-tailer", "etailer", "e-tailing", "e-tienda", "ecommerce platform", "shop online", "boutique online", "fashion store", "fashion shop", "lifestyle shop", "lifestyle store", "retail online", "tienda de ropa online", "cosmetics shop", "cosmetics store", "beauty shop", "beauty store", "sports shop", "sports store", "furniture shop", "furniture store", "decor shop", "decor store", "gift shop", "gift store", "tattoo shop", "tattoo store", "ink shop", "ink store", "muebles online", "decoracion online", "ropa online", "zapatos online", "calzado online", "accesorios online", "perfumeria online", "perfume online", "cosmetica online", "cosmética online", "maquillaje online", "jugueteria online", "juguetería online", "regalos online", "regalo online", "hogar online", "home online", "kitchen online", "cocina online", "bedroom online", "dormitorio online", "living online", "salon online", "salón online", "eventos online", "event shop", "event store"
    ],

    # Salud y ciencias de la vida
    "Salud (Hospitales y Clínicas)": [
        "salud", "hospital", "hospitales", "clinica", "clínica", "clinicas", "clínicas", "sanatorio", "sanatorios",
        "centro medico", "centro médico", "centros medicos", "emergencias", "emergencia", "urgencias", "urgencia",
        "cuidados intensivos", "medicina", "medico", "médico", "medicos", "médicos", "consultorio", "consultorios",
        "paciente", "pacientes", "enfermeria", "enfermería", "cirugia", "cirugía", "quirofano", "quirófano",
        "hospitalizacion", "hospitalización", "internacion", "internación", "ambulatorio", "ambulancia",
        "healthcare", "medical center", "medical centres", "emergency care", "intensive care", "emergency room",
        "patient care", "medical facility", "hospital network", "medical services", "clinical care", "medical practice"
    ],
    "Laboratorios y Diagnóstico": [
        "laboratorio", "laboratorios", "diagnostico", "diagnóstico", "diagnosticos", "diagnósticos", 
        "analisis clinicos", "análisis clínicos", "analisis", "análisis", "rayos x", "radiografia", "radiografía",
        "imaginologia", "imagenologia", "resonancia magnetica", "resonancia magnética", "tomografia", "tomografía",
        "ecografia", "ecografía", "ultrasonido", "analítica", "hematologia", "hematología", "bioquimica", "bioquímica",
        "microbiologia", "microbiología", "patologia", "patología", "biopsia", "cultivo", "examen", "examenes", "exámenes",
        "laboratory", "laboratories", "diagnostics", "imaging", "radiology", "pathology", "clinical analysis",
        "medical imaging", "lab services", "diagnostic center", "medical testing", "blood test", "urine test"
    ],
    "Farmacéutica y Biotecnología": [
        "farmaceutica", "farmacéutica", "farmaceutico", "farmacéutico", "farmacia", "farmacias", "medicamento", "medicamentos",
        "biotecnologia", "biotecnológica", "biotech", "investigacion clinica", "investigación clínica", "desarrollo farmaceutico",
        "ensayo clinico", "ensayos clinicos", "distribuidor farmaceutico", "distribucion farmaceutica", "droga", "drogas",
        "principio activo", "laboratorio farmaceutico", "industria farmaceutica", "fármaco", "fármacos", "vacuna", "vacunas",
        "pharma", "pharmaceutical", "biotech", "clinical trial", "clinical trials", "cmo", "cro", "drug development",
        "pharmaceutical industry", "pharma company", "biotech company", "clinical research", "drug discovery", "vaccine"
    ],
    "Telemedicina y Healthtech": [
        "telemedicina", "teleconsulta", "teleconsultas", "consulta online", "consulta virtual", "medicina digital",
        "historia clinica electronica", "historia clínica electrónica", "hce", "turnos online", "reserva online",
        "monitoreo remoto", "wearables", "salud digital", "e-health", "mhealth", "aplicacion medica", "aplicación médica",
        "plataforma medica", "plataforma médica", "software medico", "software médico", "gestion hospitalaria", "gestión hospitalaria",
        "telehealth", "telemedicine", "ehr", "emr", "digital health", "remote monitoring", "virtual care",
        "health app", "medical app", "health platform", "digital therapeutics", "remote patient monitoring"
    ],

    # Educación y Universidades (agrupado y ampliado)
    "Educación y Universidades": [
        "educacion", "educación", "escuela", "escuelas", "colegio", "colegios", "universidad", "universidades", "campus", "facultad", "facultades", "licenciatura", "licenciaturas", "posgrado", "postgrado", "maestria", "maestría", "doctorado", "phd", "mba", "carrera", "carreras", "instituto", "institutos", "academia", "academias", "estudiante", "estudiantes", "alumno", "alumnos", "docente", "docentes", "profesor", "profesores", "educativo", "educativa", "pedagogia", "pedagogía", "enseñanza", "aprendizaje", "formacion", "formación", "capacitacion", "capacitación", "curso", "cursos", "seminario", "diplomado", "taller", "workshop", "congreso", "simposio", "school", "schools", "college", "university", "universities", "campus", "faculty", "k12", "education", "educational", "student", "students", "teacher", "teaching", "learning", "training", "course", "academic", "curriculum", "professor", "lecturer", "research", "investigacion", "investigación", "postgraduate", "undergraduate", "degree", "bachelor", "master", "doctoral", "distance learning", "remote learning", "virtual classroom", "online education", "e-learning", "elearning", "edtech", "plataforma educativa", "plataformas educativas", "aula virtual", "aulas virtuales", "campus virtual", "educacion digital", "educación digital", "aprendizaje virtual", "mooc", "webinar", "webinars", "contenido educativo", "material educativo", "online course", "online courses", "learning platform", "learning platforms", "lms", "educational technology", "learning management system", "digital learning"
    ],

    # Tecnología
    "Tecnología y Software (SaaS/Cloud)": [
        "tecnologia", "tecnología", "software", "saas", "paas", "iaas", "nube", "cloud", "aplicacion", "aplicación",
        "microservicios", "api", "apis", "plataforma", "plataformas", "producto digital", "productos digitales", "devops",
        "desarrollo software", "programacion", "programación", "codigo", "código", "aplicaciones", "sistema", "sistemas",
        "solucion tecnologica", "solución tecnológica", "innovacion", "innovación", "digitalizacion", "digitalización",
        "software as a service", "cloud computing", "platform", "product-led", "microservices", "technology",
        "software development", "web application", "mobile app", "digital platform", "tech company", "software company",
        "cloud services", "digital solution", "tech solution", "software platform", "digital transformation"
    ],
    "Ciberseguridad": [
        "ciberseguridad", "seguridad informatica", "seguridad informática", "seguridad digital", "pentesting", "firewall",
        "siem", "sso", "gestor de identidades", "zero trust", "endpoint", "antivirus", "malware", "phishing",
        "vulnerabilidad", "vulnerabilidades", "hacking etico", "hacking ético", "auditoria seguridad", "auditoría seguridad",
        "proteccion datos", "protección datos", "encriptacion", "encriptación", "backup", "respaldo", "forense digital",
        "cybersecurity", "infosec", "xdr", "iam", "sso", "mfa", "edr", "cyber security", "information security",
        "data protection", "threat detection", "security audit", "penetration testing", "ethical hacking", "digital forensics"
    ],
    "IA, Datos y Analítica": [
        "inteligencia artificial", "ia", "machine learning", "aprendizaje automatico", "aprendizaje automático", "nlp",
        "vision por computadora", "visión por computadora", "big data", "analitica", "analítica", "datos", "data",
        "algoritmo", "algoritmos", "neural network", "redes neuronales", "deep learning", "chatbot", "chatbots",
        "automatizacion", "automatización", "robotic process automation", "rpa", "business intelligence", "bi",
        "data science", "ciencia de datos", "mineria de datos", "minería de datos", "predictive analytics", "data mining",
        "artificial intelligence", "ml", "deep learning", "computer vision", "analytics", "data science",
        "data analytics", "business intelligence", "predictive analytics", "machine learning", "ai company",
        "data platform", "analytics platform", "ai solution", "intelligent automation", "cognitive computing"
    ],
    "Hardware y Electrónica": [
        "hardware", "iot", "internet of things", "dispositivo", "dispositivos", "electronica", "electrónica", "placa", "placas",
        "sensor", "sensores", "fabricacion electronica", "fabricación electrónica", "semiconductor", "semiconductores",
        "circuito", "circuitos", "componente electronico", "componente electrónico", "microcontrolador", "microcontroladores",
        "embedded", "sistema embebido", "sistemas embebidos", "arduino", "raspberry pi", "microchip", "procesador",
        "electronics", "device", "embedded", "firmware", "pcb", "sensor", "semiconductor", "electronic components",
        "circuit board", "microcontroller", "embedded systems", "electronic manufacturing", "iot devices", "smart devices"
    ],
    "Cloud e Infraestructura": [
        "infraestructura", "observabilidad", "monitorizacion", "monitorización", "kubernetes", "contenedor", "contenedores",
        "cdn", "edge", "sre", "site reliability", "devops", "servidor", "servidores", "datacenter", "centro de datos",
        "hosting", "alojamiento", "vps", "servidor dedicado", "balanceador de carga", "escalabilidad", "alta disponibilidad",
        "infrastructure", "observability", "monitoring", "k8s", "containers", "cdn", "edge computing",
        "cloud infrastructure", "server management", "hosting services", "data center", "scalability", "load balancing"
    ],

    # Finanzas
    "Servicios Financieros (Banca)": [
        "banco", "banca", "finanzas", "financiero", "financiera", "creditos", "créditos", "prestamos", "préstamos",
        "hipoteca", "hipotecas", "cuenta corriente", "cuenta de ahorro", "cajero", "cajeros", "pago de servicios",
        "tarjeta de credito", "tarjeta de crédito", "inversion", "inversión", "deposito", "depósito", "interes", "interés",
        "sucursal", "sucursales", "entidad financiera", "institucion financiera", "institución financiera",
        "bank", "banking", "loans", "mortgage", "checking account", "savings account", "atm", "financial services",
        "credit card", "investment", "deposit", "interest rate", "financial institution", "commercial bank",
        # Bancos españoles específicos
        "santander", "bbva", "caixabank", "bankia", "sabadell", "bankinter", "unicaja", "ibercaja", "kutxabank",
        "abanca", "banco popular", "banco pastor", "banesto", "banco madrid", "evo banco", "openbank"
    ],
    "Fintech y Pagos": [
        "fintech", "billetera", "billeteras", "pagos", "pago", "psp", "adquirencia", "pos", "qr", "wallet", "wallets",
        "transferencias", "transferencia", "open banking", "banca abierta", "pago digital", "pagos digitales",
        "monedero digital", "criptomoneda", "criptomonedas", "blockchain", "bitcoin", "remesas", "cambio de divisas",
        "payments", "payment", "acquiring", "payment gateway", "wallet", "bnpl", "open banking", "digital payments",
        "mobile payments", "peer to peer", "p2p payments", "cryptocurrency", "digital wallet", "payment processor"
    ],
    "Seguros (Insurtech)": [
        "seguros", "seguro", "aseguradora", "aseguradoras", "poliza", "póliza", "polizas", "pólizas", "siniestralidad",
        "broker de seguros", "corredor de seguros", "agente de seguros", "prima", "primas", "cobertura", "coberturas",
        "seguro de vida", "seguro de auto", "seguro medico", "seguro médico", "seguro de hogar", "reaseguro",
        "actuario", "siniestro", "siniestros", "liquidacion", "liquidación", "insurtech",
        "insurance", "insurtech", "policy", "policies", "underwriting", "broker", "insurance agent", "premium",
        "coverage", "life insurance", "auto insurance", "health insurance", "home insurance", "reinsurance", "claims"
    ],
    "Inversiones y Capital": [
        "inversiones", "inversion", "inversión", "cartera", "carteras", "corredor de bolsa", "fondo comun", "fondo común",
        "asset management", "gestion de activos", "gestión de activos", "capital privado", "capital de riesgo",
        "venture capital", "private equity", "fondo de inversion", "fondo de inversión", "portfolio", "bolsa", "acciones",
        "bonos", "derivados", "commodity", "trading", "trader", "analista financiero", "wealth management",
        "investment", "portfolio", "brokerage", "asset management", "private equity", "venture capital",
        "investment fund", "stock exchange", "stocks", "bonds", "derivatives", "wealth management", "fund management"
    ],

    # Comercio y consumo
    "Comercio Electrónico (E-commerce)": [
        "ecommerce", "e-commerce", "comercio electronico", "comercio electrónico", "tienda online", "tiendas online",
        "carrito", "checkout", "shopify", "woocommerce", "prestashop", "marketplace", "marketplaces",
        "plataforma de comercio", "venta online", "ventas online", "catalogo online", "catálogo online",
        "dropshipping", "fulfillment", "logistica ecommerce", "logística ecommerce", "pago online",
        "e-commerce", "online store", "cart", "marketplace", "magento", "bigcommerce", "online shopping",
        "digital commerce", "online retail", "e-commerce platform", "online marketplace", "digital storefront"
    ],
    "Alimentos y Bebidas (F&B)": [
        "alimentos", "alimento", "bebidas", "bebida", "comida", "comidas", "fabrica de alimentos", "fábrica de alimentos",
        "distribuidor de alimentos", "procesamiento de alimentos", "industria alimentaria", "gastronomia", "gastronomía",
        "cocina", "chef", "restauracion", "restauración", "catering", "pasteleria", "pastelería", "panaderia", "panadería",
        "lacteos", "lácteos", "carnicos", "cárnicos", "organico", "orgánico", "natural", "saludable", "nutritivo",
        "food", "beverage", "cpg", "food processing", "foodservice", "food industry", "culinary", "organic food",
        "healthy food", "food manufacturing", "food distribution", "gourmet", "specialty food", "nutrition"
    ],

    # Agro y recursos
    "Agricultura y Agroindustria": [
        "agricultura", "agricola", "agrícola", "agro", "agroindustria", "cultivo", "cultivos", "granja", "granjas",
        "semillas", "semilla", "cosecha", "campo", "campos", "productor agropecuario", "agropecuario", "agropecuaria",
        "fertilizante", "fertilizantes", "pesticida", "pesticidas", "herbicida", "herbicidas", "invernadero", "invernaderos",
        "maquinaria agricola", "maquinaria agrícola", "tractor", "tractores", "silo", "silos", "cooperativa agricola",
        "agriculture", "farming", "agribusiness", "crop", "crops", "seed", "seeds", "farm", "farmer",
        "agricultural", "greenhouse", "fertilizer", "pesticide", "harvest", "agricultural machinery", "agtech"
    ],
    "Ganadería y Pesca": [
        "ganaderia", "ganadería", "ganado", "feedlot", "lecheria", "lechería", "pesca", "pesqueria", "pesquería",
        "acuicultura", "bovino", "bovinos", "vacuno", "vacunos", "porcino", "porcinos", "avicola", "avícola",
        "pollo", "pollos", "cerdo", "cerdos", "ovino", "ovinos", "caprino", "caprinos", "leche", "carne",
        "pescado", "mariscos", "criadero", "criaderos", "veterinario", "veterinaria", "alimento balanceado",
        "livestock", "cattle", "dairy", "fishery", "aquaculture", "poultry", "pig farming", "sheep",
        "beef", "pork", "chicken", "fish farming", "seafood", "veterinary", "animal feed", "ranch"
    ],
    "Minería y Metales": [
        "mineria", "minería", "mina", "minas", "metales", "metal", "acero", "hierro", "aluminio", "cobre", "oro", "plata",
        "extraccion", "extracción", "excavacion", "excavación", "mineral", "minerales", "metalurgia", "metalúrgica",
        "siderurgia", "siderúrgica", "fundicion", "fundición", "refineria", "refinería", "concentradora",
        "yacimiento", "yacimientos", "cantera", "canteras", "carbon", "carbón", "petroleo", "petróleo",
        "mining", "metals", "steel", "aluminum", "copper", "gold", "silver", "extraction", "metallurgy",
        "mining company", "metal processing", "ore", "quarry", "coal mining", "oil extraction", "refinery"
    ],
    "Química y Plásticos": [
        "quimica", "química", "plastico", "plástico", "plásticos", "compuesto", "compuestos", "polimero", "polímero",
        "resina", "resinas", "petroquimica", "petroquímica", "laboratorio quimico", "laboratorio químico",
        "reactivo", "reactivos", "solvente", "solventes", "farmoquimica", "farmoquímica", "pintura", "pinturas",
        "adhesivo", "adhesivos", "elastomero", "elastómero", "catalizador", "formula", "fórmula",
        "chemical", "chemicals", "plastics", "polymer", "resin", "petrochemical", "chemical industry",
        "chemical company", "polymer processing", "chemical manufacturing", "specialty chemicals", "industrial chemicals"
    ],
    "Papel, Envases y Packaging": [
        "papel", "carton", "cartón", "packaging", "envase", "envases", "empaque", "empaques", "embalaje", "embalajes",
        "impresion", "impresión", "imprenta", "imprentas", "etiqueta", "etiquetas", "caja", "cajas", "bolsa", "bolsas",
        "celulosa", "papel corrugado", "carton corrugado", "cartón corrugado", "flexografia", "flexografía",
        "offset", "editorial", "revista", "revistas", "libro", "libros", "folleto", "folletos",
        "paper", "packaging", "carton", "printing", "label", "labels", "box", "boxes", "bag", "bags",
        "corrugated", "flexography", "offset printing", "publishing", "magazine", "book", "brochure", "print shop"
    ],

    # Energía y servicios públicos
    "Energía (Petróleo y Gas)": [
        "petroleo", "petróleo", "gas", "gas natural", "oleoducto", "gasoducto", "refineria", "refinería",
        "upstream", "downstream", "exploracion", "exploración", "perforacion", "perforación", "pozo", "pozos",
        "yacimiento petrolifero", "yacimiento petrolífero", "combustible", "combustibles", "nafta", "diesel",
        "gnc", "glp", "distribucion de combustibles", "distribución de combustibles", "estacion de servicio",
        "oil", "gas", "pipeline", "refinery", "upstream", "downstream", "drilling", "oil well", "fuel",
        "petroleum", "natural gas", "oil company", "gas company", "energy company", "oil exploration", "gas station"
    ],
    "Energías Renovables": [
        "energia renovable", "energía renovable", "energias renovables", "energías renovables", "solar", "fotovoltaica",
        "eolica", "eólica", "viento", "hidraulica", "hidráulica", "geotermica", "geotérmica", "biomasa",
        "panel solar", "paneles solares", "aerogenerador", "aerogeneradores", "parque eolico", "parque eólico",
        "energia limpia", "energía limpia", "sustentable", "sostenible", "carbon neutral", "carbono neutral",
        "wind", "solar power", "pv", "renewable energy", "clean energy", "sustainable energy", "wind power",
        "solar energy", "hydroelectric", "geothermal", "biomass", "wind farm", "solar farm", "green energy"
    ],
    "Utilities (Luz, Agua, Gas)": [
        "distribuidora electrica", "distribuidora eléctrica", "electricidad", "energia electrica", "energía eléctrica",
        "agua potable", "agua", "saneamiento", "cloacas", "gas natural", "gas", "telefono", "teléfono", "telefonia", "telefonía",
        "servicio publico", "servicio público", "servicios publicos", "servicios públicos", "red electrica", "red eléctrica",
        "suministro", "medidor", "medidores", "facturacion", "facturación", "tarifa", "tarifas", "consumo",
        "utility", "electric utility", "water utility", "natural gas", "grid", "public utility", "power company",
        "water company", "gas company", "electricity", "water supply", "sewage", "utility services", "power grid"
    ],

    # Construcción, inmuebles y hogar
    "Construcción e Ingeniería": [
        "construccion", "construcción", "obra", "obras", "ingenieria", "ingeniería", "contratista", "contratistas",
        "obra civil", "obras civiles", "arquitectura", "arquitecto", "arquitectos", "proyecto", "proyectos",
        "edificacion", "edificación", "vivienda", "viviendas", "infraestructura", "carretera", "carreteras",
        "puente", "puentes", "edificio", "edificios", "demolicion", "demolición", "excavacion", "excavación",
        "construction", "engineering", "contractor", "civil works", "architecture", "architect", "building",
        "infrastructure", "road construction", "bridge", "residential construction", "commercial construction"
    ],
    "Inmobiliario y PropTech": [
        "inmobiliaria", "inmobiliarias", "bienes raices", "bienes raíces", "alquiler", "alquileres", "propiedades", "propiedad",
        "venta de propiedades", "compra de propiedades", "tasacion", "tasación", "corretaje", "martillero", "martilleros",
        "desarrolladora", "desarrolladoras", "emprendimiento inmobiliario", "proptech", "portal inmobiliario",
        "departamento", "departamentos", "casa", "casas", "oficina", "oficinas", "local comercial",
        "real estate", "property", "leasing", "proptech", "real estate agency", "property management",
        "real estate development", "apartment", "house", "office", "commercial property", "property investment"
    ],
    "Hogar, Muebles y Decoración": [
        "muebles", "mueble", "decoracion", "decoración", "hogar", "equipamiento", "electrodomesticos", "electrodomésticos", "furniture", "home decor", "appliance", "home goods", "interior design", "home improvement", "kitchen", "bathroom", "bedroom", "living room", "lighting", "home furnishing", "home accessories", "cocina", "cocinas", "baño", "baños", "dormitorio", "dormitorios", "living", "comedor", "jardin", "jardín", "iluminacion", "iluminación", "lampara", "lámparas", "cortina", "cortinas", "alfombra", "alfombras", "diseño de interiores", "interiorismo", "deco", "mobiliario", "amoblamiento", "decor store", "decor shop", "furniture shop", "furniture store", "home shop", "home store", "kitchen shop", "kitchen store", "bedroom shop", "bedroom store", "bathroom shop", "bathroom store", "lighting shop", "lighting store", "living shop", "living store", "salon shop", "salon store", "salón shop", "salón store", "jardin shop", "jardin store", "jardín shop", "jardín store"
    ],

    # Viajes, turismo y gastronomía
    "Viajes y Turismo": [
        "turismo", "turistico", "turístico", "agencia de viajes", "agencias de viajes", "tour", "tours", "excursion", "excursión",
        "paquete turistico", "paquete turístico", "pasajes", "pasaje", "vuelo", "vuelos", "hotel", "hoteles",
        "reserva", "reservas", "vacaciones", "viaje", "viajes", "destino", "destinos", "guia turistico", "guía turístico",
        "travel", "tourism", "travel agency", "tour operator", "flight", "vacation", "destination",
        "travel package", "tourist", "sightseeing", "travel booking", "holiday", "trip", "journey"
    ],
    "Hotelería y Alojamiento": [
        "hotel", "hoteles", "hostel", "hostels", "alojamiento", "alojamientos", "resort", "resorts", "spa", "spas",
        "hospedaje", "hospedajes", "posada", "posadas", "hosteria", "hostería", "apart hotel", "aparthotel",
        "habitacion", "habitación", "habitaciones", "suite", "suites", "pension", "pensión", "bed and breakfast",
        "turismo rural", "estancia", "estancias", "cabana", "cabaña", "cabañas", "camping", "glamping",
        "hotel", "lodging", "resort", "hospitality", "accommodation", "inn", "motel", "guest house",
        "vacation rental", "boutique hotel", "luxury hotel", "budget hotel", "hotel chain", "hospitality industry"
    ],
    "Restaurantes y Catering": [
        "restaurante", "restaurantes", "bar", "bares", "cafeteria", "cafeterías", "cafe", "café", "gastronomia", "gastronomía",
        "catering", "foodservice", "parrilla", "parrillas", "pizzeria", "pizzería", "heladeria", "heladería",
        "pasteleria", "pastelería", "panaderia", "panadería", "delivery", "take away", "comida rapida", "comida rápida",
        "chef", "cocinero", "menu", "menú", "carta", "cocina", "salon de eventos", "salón de eventos", "banquete",
        "restaurant", "bar", "cafe", "catering", "food service", "bistro", "fast food", "fine dining",
        "casual dining", "food delivery", "culinary", "chef", "menu", "bakery", "pastry shop", "event catering"
    ],

    # Medios, publicidad y entretenimiento
    "Medios, Publicidad y Marketing": [
        "marketing", "publicidad", "agencia", "agencias", "seo", "sem", "performance marketing", "marketing digital",
        "prensa", "pr", "relaciones publicas", "relaciones públicas", "comunicacion", "comunicación", "branding",
        "diseño grafico", "diseño gráfico", "creatividad", "campana", "campaña", "campañas", "medios", "advertising",
        "social media", "redes sociales", "influencer", "content marketing", "email marketing", "adwords", "facebook ads",
        "advertising", "media", "marketing agency", "seo", "sem", "digital marketing", "social media marketing",
        "content marketing", "brand strategy", "creative agency", "media agency", "public relations", "graphic design",
        # Outbound Marketing y Lead Generation específicos
        "outbound", "lead generation", "lead gen", "leads", "pipeline", "prospect", "prospectos", "prospecting",
        "cold email", "cold calling", "outreach", "sales development", "sdr", "bdr", "business development",
        "lead qualification", "lead scoring", "demand generation", "demand gen", "qualified leads", "leads cualificados",
        "sales funnel", "conversion", "conversiones", "growth hacking", "growth marketing", "acquisition",
        "customer acquisition", "adquisicion", "adquisición", "inbound", "inbound marketing", "marketing automation",
        "crm", "customer relationship", "sales enablement", "sales acceleration", "revenue operations", "revops",
        "account based marketing", "abm", "personalization", "segmentation", "targeting", "retargeting",
        "smartlead", "outbound partner", "certified partner", "partner certificado", "sales qualified", "mql", "sql"
    ],
    "Entretenimiento y Eventos": [
        "entretenimiento", "evento", "eventos", "ticketing", "concierto", "conciertos", "festival", "festivales", "teatro", "teatros", "cine", "espectaculo", "espectáculo", "espectáculos", "show", "shows", "musica", "música", "artista", "artistas", "productor", "productora", "organizacion de eventos", "organización de eventos", "salon de fiestas", "salón de fiestas", "wedding planner", "dj", "sonido", "iluminacion escenica", "iluminación escénica", "entertainment", "events", "ticketing", "concert", "festival", "theater", "cinema", "show", "music", "artist", "event production", "event management", "party planning", "wedding planning", "live entertainment", "event shop", "event store", "ticket shop", "ticket store", "concierto shop", "concierto store", "festival shop", "festival store", "cine shop", "cine store", "musica shop", "musica store", "show shop", "show store", "fiesta shop", "fiesta store", "wedding shop", "wedding store"
    ],
    "Deportes": [
        "futbol", "fútbol", "football", "soccer", "baloncesto", "basketball", "tenis", "tennis", "deporte", "deportes", "sport", "sports", "equipo", "team", "club deportivo", "athletic club", "cantera", "academia deportiva", "entrenamiento", "training", "estadio", "stadium", "campo deportivo", "sporting", "atletismo", "athletics", "natacion", "natación", "swimming", "gimnasia", "gymnastics", "voleibol", "volleyball", "handball", "balonmano", "rugby", "hockey", "golf", "paddle", "padel", "ciclismo", "cycling", "running", "maratón", "marathon", "primer equipo", "segunda division", "liga", "league", "championship", "campeonato", "torneos", "tournaments", "jugador", "jugadores", "players", "entrenador", "coach", "tecnico", "técnico", "athletic", "deportivo", "sports club", "football club", "basketball team", "tennis club", "golf club", "sporting club", "athletic team", "sports shop", "sports store", "deportes shop", "deportes store", "tienda de deportes", "tienda deportiva", "ropa deportiva", "calzado deportivo", "accesorios deportivos", "balones", "pelotas", "raquetas", "zapatillas deportivas", "camisetas deportivas", "equipamiento deportivo"
    ],

    # Telecom y digital
    "Telecomunicaciones e ISP": [
        "telecom", "telecomunicaciones", "telefonia", "telefonía", "telefono", "teléfono", "celular", "movil", "móvil",
        "isp", "internet", "fibra optica", "fibra óptica", "redes", "red", "antena", "antenas", "torre", "torres",
        "operador", "operadores", "conectividad", "banda ancha", "wifi", "5g", "4g", "3g", "roaming", "sms",
        "telecommunications", "mobile operator", "internet provider", "fiber", "network", "telecom company",
        "wireless", "broadband", "connectivity", "mobile network", "internet service provider", "telecommunication services"
    ],

    # Servicios profesionales y legales
    "Consultoría y Servicios Profesionales": [
        "consultoria", "consultoría", "consultor", "consultores", "asesoria", "asesoría", "asesor", "asesores",
        "servicios profesionales", "outsourcing", "tercerizacion", "tercerización", "subcontratacion", "subcontratación",
        "estrategia", "implementacion", "implementación", "transformacion", "transformación", "eficiencia", "procesos",
        "auditoria", "auditoría", "advisory", "business intelligence", "gestion", "gestión", "administracion", "administración",
        "consulting", "advisory", "professional services", "outsourcing", "business consulting", "management consulting",
        "strategy consulting", "implementation", "business process", "process improvement", "business transformation"
    ],
    "Legal y Estudios Jurídicos": [
        "abogado", "abogados", "estudio juridico", "estudio jurídico", "estudios juridicos", "estudios jurídicos",
        "legal", "derecho", "juridico", "jurídico", "contratos", "contrato", "litigio", "litigios", "compliance",
        "asesoria legal", "asesoría legal", "notario", "notarios", "escribano", "escribanos", "mediacion", "mediación",
        "arbitraje", "tribunal", "corte", "juzgado", "fiscal", "procurador", "defensor", "bufete",
        "law firm", "legal services", "attorney", "lawyer", "litigation", "compliance", "legal advice",
        "legal counsel", "law office", "legal consulting", "paralegal", "legal practice", "jurisprudence"
    ],
    "Recursos Humanos y Staffing": [
        "recursos humanos", "rrhh", "hr", "seleccion", "selección", "reclutamiento", "headhunting", "headhunter",
        "staffing", "payroll", "nomina", "nómina", "liquidacion de sueldos", "liquidación de sueldos", "cazatalentos",
        "busqueda ejecutiva", "búsqueda ejecutiva", "capacitacion", "capacitación", "entrenamiento", "coaching",
        "evaluacion de desempeño", "evaluación de desempeño", "clima laboral", "cultura organizacional", "onboarding",
        "human resources", "recruiting", "recruitment", "headhunter", "staffing", "payroll", "talent acquisition",
        "hr services", "workforce management", "employee training", "performance management", "hr consulting"
    ],

    # Textil, calzado y afines (manufactura consumo)
    "Textil y Confección": [
        "textil", "textiles", "tela", "telas", "confeccion", "confección", "manufactura textil", "industria textil",
        "hilado", "tejido", "tintura", "estampado", "bordado", "costura", "maquila", "hilanderia", "hilandería",
        "algodon", "algodón", "lana", "seda", "fibra", "fibras", "denim", "jean", "uniforme", "uniformes",
        "textile", "garment manufacturing", "spinning", "weaving", "fabric", "cotton", "wool", "silk",
        "textile industry", "garment industry", "clothing manufacturing", "textile production", "fashion manufacturing"
    ],

    # Sector público y social
    "Gobierno y Sector Público": [
        "gobierno", "gubernamental", "municipio", "municipalidad", "provincia", "estado", "ministerio", "ministerios",
        "secretaria", "secretaría", "organismo publico", "organismo público", "entidad publica", "entidad pública",
        "administracion publica", "administración pública", "sector publico", "sector público", "municipalidad",
        "intendencia", "gobernacion", "gobernación", "concejo", "camara", "cámara", "senado", "congreso", "parlamento",
        "government", "public sector", "ministry", "municipal", "state government", "federal government",
        "public administration", "government agency", "public entity", "city hall", "county government", "parliament"
    ],
    "ONG y Sin Fines de Lucro": [
        "ong", "ongs", "fundacion", "fundación", "fundaciones", "sin fines de lucro", "no lucrativo", "no lucrativa",
        "asociacion civil", "asociación civil", "organizacion no gubernamental", "organización no gubernamental",
        "beneficencia", "caridad", "solidaridad", "voluntariado", "donacion", "donación", "donaciones", "filantropia", "filantropía",
        "causa social", "impacto social", "tercer sector", "sociedad civil", "ayuda humanitaria", "cooperacion", "cooperación",
        "nonprofit", "ngo", "charity", "foundation", "non-profit organization", "charitable organization",
        "social impact", "humanitarian", "volunteer", "philanthropy", "social cause", "civil society"
    ],
}

# ============================================================
# DETECCIÓN CON SCORE
# - Cuenta coincidencias de keywords por industria
# - Devuelve top_k industrias con mayor score
# - También devuelve keywords que matchearon (útil para debug)
# ============================================================

def _score_text(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    """
    Improved scoring function that considers word boundaries and keyword weights.
    Uses word boundaries for potentially ambiguous words to avoid false positives.
    Filters out technical/CSS contexts for ambiguous automotive terms.
    """
    import re
    low = text.lower()
    hits = []
    score = 0
    
    # Palabras que SIEMPRE deben usar word boundaries para evitar falsos positivos
    word_boundary_required = {
        "car", "cars", "auto", "autos", "vehicle", "vehicles", "motor", "battery", 
        "engine", "tire", "tires", "api", "app", "data", "web", "tech", "digital",
        "online", "internet", "software", "hardware", "system", "network", "cloud",
        "mobile", "phone", "email", "mail", "shop", "store", "market", "service",
        "services", "product", "products", "business", "company", "enterprise"
    }
    
    # Palabras que son muy ambiguas y necesitan contexto específico para evitar falsos positivos
    highly_ambiguous = {"auto", "car", "cars", "motor", "battery", "engine", "data", "app", "api"}
    
    for kw in keywords:
        kw_lower = kw.lower()
        
        # Usar word boundaries si la palabra está en la lista de ambiguas O es muy corta
        if kw_lower in word_boundary_required or len(kw_lower) <= 3:
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            matches = re.finditer(pattern, low)
            
            valid_matches = 0
            for match in matches:
                # Para palabras muy ambiguas, verificar que no estén en contexto técnico
                if kw_lower in highly_ambiguous:
                    # Obtener contexto alrededor del match
                    start = max(0, match.start() - 50)
                    end = min(len(low), match.end() + 50)
                    context = low[start:end]
                    
                    # Skipear si está en contexto técnico/CSS/HTML
                    if any(tech_term in context for tech_term in [
                        "width:", "height:", "size=", "auto-", "-auto", "margin-", 
                        "padding-", "flex:", "grid-", "overflow:", "css", "style",
                        "px", "rem", "vh", "vw", "auto;", "auto,", "auto }", "auto)", 
                        "sizes=", "generated", "preset", "wp-", "elementor",
                        # Para 'data': contextos técnicos
                        "data-", "-data", "dataset", "metadata", "data:", "data=",
                        "data{", "data}", "data[", "data]", "json", "javascript",
                        "script", "<script", "element_type", "data_id", "data_element"
                    ]):
                        continue
                
                valid_matches += 1
            
            if valid_matches > 0:
                # Palabras más largas tienen más peso
                keyword_weight = max(0.5, min(2.0, len(kw_lower) / 4.0))
                score += keyword_weight * valid_matches
                hits.append(kw)
        else:
            # Para keywords largas y específicas, substring + bonus si es palabra completa
            if kw_lower in low:
                keyword_weight = min(2.0, len(kw_lower) / 5.0)
                score += keyword_weight
                hits.append(kw)
                # Bonus si es palabra completa
                pattern = r'\b' + re.escape(kw_lower) + r'\b'
                if re.search(pattern, low):
                    score += 0.5
    
    return int(score), hits


def _apply_domain_specific_rules(domain: str, texto: str, resultados: List[Dict]) -> List[Dict]:
    """
    Aplica reglas específicas basadas en el dominio para mejorar la precisión
    """
    domain_lower = domain.lower()
    
    # Reglas específicas para bancos españoles
    banking_domains = [
        'santander', 'bbva', 'caixabank', 'bankinter', 'sabadell', 'unicaja', 
        'ibercaja', 'kutxabank', 'abanca', 'openbank', 'evo'
    ]
    
    if any(bank in domain_lower for bank in banking_domains):
        # Forzar clasificación bancaria si es un dominio bancario conocido
        banking_score = 100  # Score muy alto para forzar
        resultados.insert(0, {
            "industria": "Servicios Financieros (Banca)", 
            "score": banking_score, 
            "keywords": ["domain_rule"]
        })
    
    # Reglas para energía
    energy_domains = ['endesa', 'iberdrola', 'naturgy', 'repsol', 'eon', 'edp']
    if any(energy in domain_lower for energy in energy_domains):
        energy_score = 100
        resultados.insert(0, {
            "industria": "Energía y Utilities", 
            "score": energy_score, 
            "keywords": ["domain_rule"]
        })
    
    # Reglas para telecomunicaciones
    telecom_domains = ['telefonica', 'vodafone', 'orange', 'movistar', 'jazztel']
    if any(telecom in domain_lower for telecom in telecom_domains):
        telecom_score = 100
        resultados.insert(0, {
            "industria": "Telecomunicaciones e ISP", 
            "score": telecom_score, 
            "keywords": ["domain_rule"]
        })
    
    # Reglas para retail/fashion
    retail_domains = ['zara', 'mango', 'inditex', 'corteingles', 'mercadona', 'carrefour']
    if any(retail in domain_lower for retail in retail_domains):
        retail_score = 100
        resultados.insert(0, {
            "industria": "Retail y E-commerce", 
            "score": retail_score, 
            "keywords": ["domain_rule"]
        })
    
    # Reglas para medios
    media_domains = ['atresmedia', 'mediaset', 'prisa', 'planeta']
    if any(media in domain_lower for media in media_domains):
        media_score = 100
        resultados.insert(0, {
            "industria": "Medios, Publicidad y Marketing", 
            "score": media_score, 
            "keywords": ["domain_rule"]
        })
    
    return resultados


def _detectar_industria_por_dominio(domain: str) -> Optional[str]:
    """Mapeo directo de dominios conocidos a industrias"""
    domain_mappings = {
        # Bancos españoles
        "santander.com": "Servicios Financieros (Banca)",
        "bbva.com": "Servicios Financieros (Banca)",
        "caixabank.es": "Servicios Financieros (Banca)",
        "bankinter.com": "Servicios Financieros (Banca)",
        "sabadell.com": "Servicios Financieros (Banca)",
        "bankia.es": "Servicios Financieros (Banca)",
        
        # Energía españolas
        "endesa.com": "Energía y Utilities",
        "iberdrola.es": "Energía y Utilities",
        "naturgy.com": "Energía y Utilities",
        "repsol.com": "Energía y Utilities",
        "cepsa.com": "Energía y Utilities",
        
        # Telecomunicaciones
        "telefonica.com": "Telecomunicaciones e ISP",
        "vodafone.es": "Telecomunicaciones e ISP",
        "orange.es": "Telecomunicaciones e ISP",
        "movistar.es": "Telecomunicaciones e ISP",
        
        # Retail/Fashion
        "zara.com": "Retail y E-commerce",
        "inditex.com": "Retail y E-commerce",
        "elcorteingles.es": "Retail y E-commerce",
        "mercadona.es": "Retail y E-commerce",
        
        # Medios
        "atresmedia.com": "Medios, Publicidad y Marketing",
        "mediaset.es": "Medios, Publicidad y Marketing",
        
        # Construcción
        "acs.es": "Construcción e Inmobiliaria",
        "ferrovial.com": "Construcción e Inmobiliaria",
        
        # Aerolíneas
        "iberia.com": "Turismo y Viajes",
        "vueling.com": "Turismo y Viajes",
    }
    
    # Buscar coincidencia exacta
    if domain in domain_mappings:
        return domain_mappings[domain]
    
    # Buscar sin www
    clean_domain = domain.replace("www.", "")
    if clean_domain in domain_mappings:
        return domain_mappings[clean_domain]
    
    return None


def _apply_domain_specific_rules(domain: str, texto: str, resultados: List[Dict]) -> List[Dict]:
    """Aplica reglas específicas basadas en el dominio"""
    # Primero intentar mapeo directo
    direct_industry = _detectar_industria_por_dominio(domain)
    if direct_industry:
        # Si encontramos mapeo directo, priorizarlo
        for result in resultados:
            if result["industria"] == direct_industry:
                result["score"] += 10  # Boost significativo
                break
        else:
            # Si no estaba en los resultados, agregarlo
            resultados.append({
                "industria": direct_industry,
                "score": 15,  # Score alto para domain mapping
                "keywords": ["domain_mapping"]
            })
    
    return resultados


def detectar_industrias(texto: str, domain: str = "", top_k: int = 2, min_score: int = 1) -> List[Dict[str, object]]:
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
    
    # Aplicar reglas específicas de dominio
    if domain:
        resultados = _apply_domain_specific_rules(domain, texto, resultados)
    
    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados[:top_k]


def detectar_principal_y_secundaria(texto: str, domain: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Azúcar: devuelve (principal, secundaria) o (None, None).
    """
    top = detectar_industrias(texto, domain, top_k=2, min_score=1)
    if not top:
        return None, None
    if len(top) == 1:
        return top[0]["industria"], None
    return top[0]["industria"], top[1]["industria"]
