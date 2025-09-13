# GTM Scanner API Documentation

## 🚀 Quick Start

### Base URL
```
https://your-render-app.onrender.com
```

### Health Check
```bash
GET /
```

## 📡 Main Endpoint

### POST /scan

Analiza un sitio web y retorna inteligencia empresarial completa con enrichment de datos externos.

#### Request Body
```json
{
  "domain": "example.com",           // Required: Domain to scan
  "max_pages": 3,                   // Optional: Max pages to crawl (default: 8)
  "company_name": "Company Name",    // Optional: Company name hint
  "timeout_sec": 10,                // Optional: Request timeout (default: 10)
  "respect_robots": true            // Optional: Respect robots.txt (default: true)
}
```

#### Response Structure
```json
{
  "domain": "example.com",
  "company_name": "Example Company",
  "context": {
    "summary": "Brief company description"
  },
  "social": {
    "linkedin": "https://linkedin.com/company/example",
    "twitter": "https://twitter.com/example",
    "emails": ["contact@example.com"]
  },
  "industry": "Technology",
  "industry_secondary": "SaaS",
  "tech_stack": {
    "CMS": {
      "tools": ["WordPress"],
      "evidence": "wp-content|wp-includes"
    },
    "Analytics": {
      "tools": ["Google Analytics 4"],
      "evidence": "gtag('config','G-"
    }
  },
  "enrichment": {
    "domain_intelligence": {
      "hosting_provider": "AWS",
      "email_provider": "Google Workspace",
      "hosting_ip": "52.29.175.16",
      "response_time_ms": 1
    },
    "business_intelligence": {
      "business_type": "E-commerce Platform",
      "location": "Global",
      "confidence": "High",
      "response_time_ms": 543
    },
    "local_presence": {
      "business_verified": true,
      "rating": 4.2,
      "review_count": 245,
      "business_hours": "24 horas",
      "response_time_ms": 521
    },
    "enrichment_timing": {
      "total_time_ms": 548,
      "sources_found": 3
    }
  },
  "seo_metrics": {
    "meta_title_length": 60,
    "meta_description_length": 155,
    "has_structured_data": true,
    "page_load_time_ms": 234,
    "h1_count": 1,
    "h2_count": 3,
    "internal_links_count": 25,
    "external_links_count": 8,
    "page_size_kb": 125.4
  },
  "pages_crawled": [
    "https://example.com",
    "https://example.com/about"
  ],
  "recent_news": []
}
```

## 🌐 Enrichment Details

### Domain Intelligence
- **hosting_provider**: AWS, Google Cloud, Azure, Cloudflare
- **email_provider**: Google Workspace, Microsoft 365, etc.
- **hosting_ip**: Server IP address
- **response_time_ms**: DNS lookup time

### Business Intelligence  
- **business_type**: E-commerce, Technology, Hotel, Manufacturing, etc.
- **location**: Global, Spain, Latin America, etc.
- **confidence**: High (reliable detection), Medium (basic inference)
- **response_time_ms**: Business analysis time

### Local Presence
- **business_verified**: Business has local presence
- **rating**: Google Reviews rating (1.0-5.0)
- **review_count**: Number of reviews
- **business_hours**: Operating hours
- **response_time_ms**: Maps lookup time

## ⚡ Performance

### Response Times
- **Fast sites**: 0.5-1.0s total
- **Medium sites**: 1.0-2.0s total  
- **Slow sites**: 2.0-3.0s total
- **Enrichment**: +0.5-1.0s (parallel execution)

### Timeouts
- **Ultra-fast**: 2s timeout
- **Fast**: 5s timeout
- **Normal**: 8s timeout (final attempt)

## 🚨 Error Handling

### 404 - Website Not Accessible
```json
{
  "detail": {
    "error": "Website not accessible",
    "domain": "example.com",
    "resolved_url": "https://example.com",
    "details": "Website did not respond after 3 attempts (2s, 5s, 8s timeouts)",
    "attempts": [
      "Attempt 1 (ultra-fast): No HTML returned",
      "Attempt 2 (fast): No HTML returned", 
      "Attempt 3 (normal): No HTML returned"
    ],
    "suggestions": [
      "Website might be down or very slow",
      "Try again in a few minutes",
      "Check if website loads in browser",
      "Website might block automated requests"
    ]
  }
}
```

### 500 - Internal Server Error
```json
{
  "detail": "Internal server error with diagnostic information"
}
```

## 🎯 Use Cases

### Sales Intelligence
```bash
curl -X POST "https://your-app.onrender.com/scan" \
  -H "Content-Type: application/json" \
  -d '{"domain": "prospect-company.com"}'
```

### Competitive Analysis
```bash
curl -X POST "https://your-app.onrender.com/scan" \
  -H "Content-Type: application/json" \
  -d '{"domain": "competitor.com", "max_pages": 5}'
```

### Lead Qualification
```bash
curl -X POST "https://your-app.onrender.com/scan" \
  -H "Content-Type: application/json" \
  -d '{"domain": "lead-website.com", "company_name": "Lead Company"}'
```