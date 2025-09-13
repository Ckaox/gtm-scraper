# GTM Scanner - Comprehensive Website Intelligence Tool

A powerful FastAPI-based tool for comprehensive website analysis and Go-To-Market (GTM) intelligence gathering.

## 🎯 Overview

GTM Scanner analyzes websites to extract valuable business intelligence including company information, technology stack, industry classification, SEO metrics, and competitive insights. Perfect for sales teams, market researchers, and business development professionals.

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Running the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Basic Usage
```bash
curl -X POST "http://localhost:8080/scan" \
     -H "Content-Type: application/json" \
     -d '{"domain": "https://example.com"}'
```

## 📊 Output Structure

The scanner returns data in the following optimized order:

### 1. Domain & Company Name
- **Domain**: Normalized domain name
- **Company Name**: Extracted using multiple methods:
  - JSON-LD structured data
  - OpenGraph site_name
  - Page title analysis
  - H1 tag analysis
  - Domain name cleanup
  - Fallback mechanisms

### 2. Context Analysis
- **Bullets**: Key business information points (max 8)
  - Prioritizes service/product descriptions
  - Filters out legal/cookie notices
  - Focuses on business-relevant content

### 3. Social & Communication
- **Social Networks**: LinkedIn, Twitter, Facebook, Instagram, YouTube, GitHub, TikTok
- **Emails**: Extracted email addresses (max 5, integrated into social section)
- **Contact Information**: Contact page URLs

### 4. Industry Classification
- **Primary Industry**: Main business sector
- **Secondary Industry**: Additional business areas
- **Advanced Scoring**: Uses keyword density with word boundary matching
- **50+ Industry Categories**: From healthcare to fintech to manufacturing

### 5. Technology Stack
Organized by categories instead of individual tools:
- **CMS**: WordPress, Webflow, Shopify, etc.
- **Analytics**: Google Analytics, GTM, Segment, etc.
- **Marketing Automation**: HubSpot, Marketo, Mailchimp, etc.
- **E-commerce**: Shopify, WooCommerce, Magento, etc.
- **JavaScript Frameworks**: React, Vue, Angular, etc.
- **And 15+ more categories**

### 6. Competitors
- Automatically detected from website content
- Based on industry context and mentions

### 7. SEO Metrics
Comprehensive SEO analysis including:
- **Meta Title Length**: Character count for SEO optimization
- **Meta Description Length**: Character count analysis
- **Structured Data**: JSON-LD, microdata detection
- **Page Load Time**: Request time in milliseconds
- **Heading Structure**: H1, H2 count analysis
- **Image Optimization**: Missing alt text count
- **Link Analysis**: Internal vs external link counts
- **Page Size**: Estimated size in KB

## 🔧 API Configuration

### Request Parameters
```json
{
  "domain": "https://example.com",
  "max_pages": 6,
  "extra_urls": [],
  "careers_overrides": [],
  "respect_robots": true,
  "timeout_sec": 10,
  "company_name": "Optional Company Name",
  "company_linkedin": "https://linkedin.com/company/example"
}
```

### Response Fields

#### Core Data (Always Present)
- `domain`: Target domain
- `company_name`: Extracted company name
- `context`: Business context bullets

#### Conditional Data (Only if Found)
- `social`: Social networks and emails
- `industry`: Primary industry classification
- `industry_secondary`: Secondary industry
- `tech_stack`: Technology categories and tools
- `competitors`: Detected competitors
- `seo_metrics`: SEO performance metrics
- `recent_news`: Latest 3 news items
- `contact_pages`: Contact page URLs
- `pages_crawled`: All analyzed URLs

## 📈 SEO Metrics Explained

### Meta Title Length
- **Optimal**: 50-60 characters
- **Purpose**: Search engine result display
- **Impact**: Click-through rates

### Meta Description Length
- **Optimal**: 150-160 characters
- **Purpose**: Search snippet preview
- **Impact**: User engagement

### Page Load Time
- **Good**: < 2000ms
- **Average**: 2000-4000ms
- **Poor**: > 4000ms
- **Impact**: User experience and SEO ranking

### Structured Data
- **JSON-LD**: Rich snippets enablement
- **Microdata**: Enhanced search results
- **Impact**: Search visibility

### Heading Structure
- **H1 Count**: Should be 1 per page
- **H2 Count**: Content organization
- **Impact**: Content hierarchy and SEO

### Image Optimization
- **Alt Text Missing**: Accessibility concern
- **Impact**: SEO and accessibility compliance

### Link Analysis
- **Internal Links**: Site navigation strength
- **External Links**: Authority and relevance
- **Impact**: Page authority and user experience

## 🏭 Industry Categories

The scanner identifies 50+ industries including:

### Technology
- Software & SaaS
- Cybersecurity
- AI & Analytics
- Hardware & Electronics
- Cloud & Infrastructure

### Healthcare
- Hospitals & Clinics
- Pharmaceutical & Biotech
- Medical Devices
- Telemedicine

### Finance
- Banking Services
- Fintech & Payments
- Insurance
- Investment Management

### Commerce
- E-commerce
- Retail
- Fashion & Apparel
- Food & Beverage

### And many more...

## 🎯 Technology Detection

### Categories Detected
1. **CMS**: Content Management Systems
2. **E-commerce**: Online store platforms
3. **Analytics**: Traffic and behavior tracking
4. **Marketing Automation**: Email and lead management
5. **Live Chat**: Customer support tools
6. **CRM**: Customer relationship management
7. **A/B Testing**: Conversion optimization
8. **Advertising**: Marketing pixels and tags
9. **CDN**: Content delivery networks
10. **JavaScript Frameworks**: Frontend technologies
11. **CSS Frameworks**: Styling libraries
12. **Security**: Protection and verification
13. **Performance**: Speed optimization
14. **Maps**: Location services
15. **Forms**: Data collection tools
16. **Payment**: Transaction processing

## ⚡ Performance Optimizations

### Free Tier Optimizations
- Maximum 6 pages crawled
- HTML size limit: 1MB per page
- Maximum 15 technology detections
- Timeout: 10 seconds per request
- Connection limits for shared hosting

### Speed Improvements
- Early breaking in tech detection
- Prioritized content extraction
- Efficient HTML parsing
- Smart candidate URL selection

## 🛠️ Development

### Project Structure
```
app/
├── main.py              # FastAPI application
├── schemas.py           # Pydantic models
├── fetch.py            # HTTP client with caching
├── util.py             # Utility functions
└── parsers/
    ├── company_name.py  # Company name extraction
    ├── industry.py      # Industry classification
    ├── techstack.py     # Technology detection
    ├── seo_metrics.py   # SEO analysis
    ├── emails.py        # Email extraction
    ├── context.py       # Content analysis
    ├── competitors.py   # Competitor detection
    └── news.py          # News extraction
```

### Key Features Removed for Performance
- **GTM Score**: Complex scoring algorithm
- **Feeds**: RSS/Atom feed discovery
- **Bullets**: Reduced from 10 to 8 items
- **LinkedIn Intelligence**: Heavy API calls
- **Growth Signals**: Complex analysis

## 🚀 Deployment

### Render.com (Free Tier)
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

## 📝 License

This project is available for commercial and non-commercial use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and feature requests, please create an issue in the repository.

---

**GTM Scanner** - Turning websites into actionable business intelligence.