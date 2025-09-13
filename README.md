# GTM Scanner - Herramienta Ultra-Optimizada de Inteligencia Web

Una potente herramienta basada en FastAPI para análisis integral de sitios web con **enrichment de datos externos** y optimizaciones avanzadas para equipos de outbound sales.

## 🎯 Descripción General

GTM Scanner analiza sitios web en **<2 segundos** extrayendo:
- **Información empresarial** completa
- **Stack tecnológico** detallado  
- **Clasificación de industria** inteligente
- **Métricas SEO** optimizadas
- **🌐 Enrichment externo**: DNS Intelligence + Business Intelligence + Local Presence

Perfecto para equipos de **ventas**, **investigación de mercado** y **outbound sales**.

## 🚀 Inicio Rápido

### Instalación
```bash
pip install -r requirements.txt
```

### Ejecutar el Servidor
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Uso Básico
```bash
curl -X POST "http://localhost:8000/scan" \
     -H "Content-Type: application/json" \
     -d '{"domain": "example.com"}'
```

## ⚡ Optimizaciones Ultra-Rápidas

- **Timeouts escalonados**: 2s → 5s → 8s para máxima compatibilidad
- **Caché inteligente** de resolución de dominios
- **Processing paralelo** de todas las fuentes de datos
- **Enrichment asíncrono** sin impacto en performance

## 🌐 Enrichment de Datos Externos

### DNS Intelligence (1ms)
```json
{
  "hosting_provider": "AWS",
  "email_provider": "Google Workspace", 
  "hosting_ip": "52.29.175.16"
}
```

### Business Intelligence (300-900ms)
```json
{
  "business_type": "E-commerce Platform",
  "location": "Global",
  "confidence": "High"
}
```

### Local Presence (400-800ms)  
```json
{
  "rating": 4.2,
  "review_count": 245,
  "business_hours": "24 horas"
}
```

## 📊 Estructura de Salida

El escáner devuelve datos en el siguiente orden optimizado:

### 1. Dominio y Nombre de Empresa
- **Dominio**: Nombre de dominio normalizado
- **Nombre de Empresa**: Extraído usando múltiples métodos:
  - Datos estructurados JSON-LD
  - OpenGraph site_name
  - Análisis del título de página
  - Análisis de etiquetas H1
  - Limpieza del nombre de dominio
  - Mecanismos de respaldo

### 2. Análisis de Contexto
- **Contexto**: Información empresarial clave simplificada
  - Prioriza descripciones de servicios/productos
  - Filtra avisos legales/cookies
  - Se enfoca en contenido relevante para el negocio

### 3. Redes Sociales y Comunicación
- **Redes Sociales**: LinkedIn, Twitter, Facebook, Instagram, YouTube, GitHub, TikTok
- **Emails**: Direcciones de correo extraídas (máximo 5, integradas en sección social)
- **Filtrado Mejorado**: Excluye páginas de privacidad, términos legales y cookies

### 4. Clasificación de Industria
- **Industria Principal**: Sector empresarial principal
- **Industria Secundaria**: Áreas empresariales adicionales
- **Puntuación Avanzada**: Usa densidad de palabras clave con coincidencia de límites de palabra
- **50+ Categorías de Industria**: Desde salud hasta fintech y manufactura

### 5. Stack Tecnológico
Organizado por categorías en lugar de herramientas individuales:
- **CMS**: WordPress, Webflow, Shopify, etc.
- **Analytics**: Google Analytics, GTM, Segment, etc.
- **Marketing Automation**: HubSpot, Marketo, Mailchimp, etc.
- **E-commerce**: Shopify, WooCommerce, Magento, etc.
- **JavaScript Frameworks**: React, Vue, Angular, etc.
- **Y 15+ categorías más**

**🎉 Mejora Importante**: El tech_stack ahora muestra categorías como claves del diccionario (ej: "Analytics", "CMS") en lugar de índices numerados confusos (0-8).

### 6. Métricas SEO
Análisis SEO integral incluyendo:
- **Longitud Meta Title**: Conteo de caracteres para optimización SEO
- **Longitud Meta Description**: Análisis de conteo de caracteres
- **Datos Estructurados**: Detección de JSON-LD, microdata
- **Tiempo de Carga**: Tiempo de request en milisegundos
- **Estructura de Encabezados**: Análisis de conteo H1, H2
- **Optimización de Imágenes**: Conteo de texto alt faltante
- **Análisis de Enlaces**: Conteo de enlaces internos vs externos
- **Tamaño de Página**: Tamaño estimado en KB

## 🔧 Configuración de API

### Parámetros de Request
```json
{
  "domain": "https://example.com",
  "max_pages": 3,
  "timeout_sec": 10,
  "company_name": "Nombre de Empresa Opcional"
}
```

### Campos de Respuesta

#### Datos Principales (Siempre Presentes)
- `domain`: Dominio objetivo
- `company_name`: Nombre de empresa extraído
- `context`: Contexto empresarial simplificado

#### Datos Condicionales (Solo si se Encuentran)
- `social`: Redes sociales y emails
- `industry`: Clasificación de industria principal (mejorada con BI)
- `industry_secondary`: Industria secundaria
- `tech_stack`: Categorías y herramientas tecnológicas
- `seo_metrics`: Métricas de rendimiento SEO
- `enrichment`: 🌐 **NUEVO** - Datos externos (DNS + Business + Maps)
- `recent_news`: Últimos 3 elementos de noticias
- `pages_crawled`: Todas las URLs analizadas

#### 🌐 Enrichment (Datos Externos)
```json
{
  "enrichment": {
    "domain_intelligence": {
      "hosting_provider": "AWS",
      "email_provider": "Google Workspace",
      "hosting_ip": "52.29.175.16"
    },
    "business_intelligence": {
      "business_type": "E-commerce Platform", 
      "location": "Global",
      "confidence": "High"
    },
    "local_presence": {
      "rating": 4.2,
      "review_count": 245,
      "business_hours": "24 horas"
    }
  }
}
```

## 📈 Métricas SEO Explicadas

### Longitud Meta Title
- **Óptimo**: 50-60 caracteres
- **Propósito**: Visualización en resultados de búsqueda
- **Impacto**: Tasas de clics

### Longitud Meta Description
- **Óptimo**: 150-160 caracteres
- **Propósito**: Vista previa del snippet de búsqueda
- **Impacto**: Engagement del usuario

### Tiempo de Carga de Página
- **Bueno**: < 2000ms
- **Promedio**: 2000-4000ms
- **Malo**: > 4000ms
- **Impacto**: Experiencia del usuario y ranking SEO

### Datos Estructurados
- **JSON-LD**: Habilitación de rich snippets
- **Microdata**: Resultados de búsqueda mejorados
- **Impacto**: Visibilidad en búsquedas

## 🏭 Categorías de Industria

El escáner identifica 50+ industrias incluyendo:

### Tecnología
- Software & SaaS
- Ciberseguridad
- IA & Analytics
- Hardware & Electrónicos
- Cloud & Infraestructura

### Salud
- Hospitales & Clínicas
- Farmacéutica & Biotech
- Dispositivos Médicos
- Telemedicina

### Finanzas
- Servicios Bancarios
- Fintech & Pagos
- Seguros
- Gestión de Inversiones

### Comercio
- E-commerce
- Retail
- Moda & Vestimenta
- Comida & Bebidas

### Y muchas más...

## 🎯 Detección de Tecnología

### Categorías Detectadas
1. **CMS**: Sistemas de Gestión de Contenido
2. **E-commerce**: Plataformas de tienda online
3. **Analytics**: Seguimiento de tráfico y comportamiento
4. **Marketing Automation**: Gestión de email y leads
5. **Live Chat**: Herramientas de soporte al cliente
6. **CRM**: Gestión de relaciones con clientes
7. **A/B Testing**: Optimización de conversiones
8. **Advertising**: Píxeles y tags de marketing
9. **CDN**: Redes de entrega de contenido
10. **JavaScript Frameworks**: Tecnologías frontend
11. **CSS Frameworks**: Librerías de estilos
12. **Security**: Protección y verificación
13. **Performance**: Optimización de velocidad
14. **Maps**: Servicios de localización
15. **Forms**: Herramientas de recopilación de datos
16. **Payment**: Procesamiento de transacciones

## ⚡ Optimizaciones de Rendimiento

### Optimizaciones para Hosting Gratuito
- Máximo 3 páginas crawleadas (reducido de 6)
- Límite de tamaño HTML: 1MB por página
- Máximo 8 detecciones tecnológicas por categoría
- Timeout: 8-10 segundos por request
- Límites de conexión para hosting compartido

### Mejoras de Velocidad
- Detención temprana en detección de tecnología
- Extracción de contenido priorizada
- Parsing HTML eficiente
- Selección inteligente de URLs candidatas
- Procesamiento limitado de noticias y emails

## 🛠️ Desarrollo

### Estructura del Proyecto
```
app/
├── main.py              # Aplicación FastAPI
├── schemas.py           # Modelos Pydantic
├── fetch.py            # Cliente HTTP con caché
├── util.py             # Funciones de utilidad
└── parsers/
    ├── company_name.py  # Extracción de nombre de empresa
    ├── industry.py      # Clasificación de industria
    ├── techstack.py     # Detección de tecnología
    ├── seo_metrics.py   # Análisis SEO
    ├── emails.py        # Extracción de emails
    └── news.py          # Extracción de noticias
```

### Características Eliminadas para Rendimiento
- **Bullets**: Análisis de contexto detallado (eliminado completamente)
- **Competitors**: Detección de competidores (eliminado - siempre vacío)
- **Contact Pages**: Páginas de contacto (eliminado - no se usaba)
- **Feeds**: Descubrimiento de feeds RSS/Atom (eliminado)
- **LinkedIn Intelligence**: Llamadas pesadas a API (eliminado)
- **Growth Signals**: Análisis complejo (eliminado)

## 🚀 Despliegue

### Render.com (Nivel Gratuito)
```yaml
# render.yaml
services:
  - type: web
    name: gtm-scanner
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 🧪 Resultados de Pruebas

### ✅ Rendimiento Optimizado
```
GitHub.com: 1.90s ⚡
Hospital Italiano: 3.34s ✅  
Google.com: 0.08s ⚡⚡⚡
```

### ✅ Dominios Problemáticos Resueltos
```
galiciamaxica.eu: ✅ 0.46s (funciona con redirección)
acrylicosvallejo.com: ✅ 0.65s (funciona correctamente)
kaioland.com: ✅ 0.28s (funciona con www)
```

**Tiempo promedio**: 0.47s para dominios problemáticos

## 📝 Licencia

Este proyecto está disponible para uso comercial y no comercial.

## 🤝 Contribuciones

1. Fork del repositorio
2. Crear una rama de feature
3. Hacer tus cambios
4. Agregar tests si aplica
5. Enviar un pull request

## 📞 Soporte

Para problemas y solicitudes de features, por favor crear un issue en el repositorio.

---

**GTM Scanner** - Convirtiendo sitios web en inteligencia empresarial accionable.