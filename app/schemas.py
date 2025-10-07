# app/app/schemas.py
from pydantic import BaseModel, AnyHttpUrl, Field, field_validator
from typing import List, Optional, Dict, Any

# -------- Inputs

class ScanRequest(BaseModel):
    domain: Optional[str] = None
    domains: Optional[List[str]] = None
    max_pages: int = Field(default=12, ge=1, le=30)  # Aumentado de 8 a 12 por defecto, máximo de 30
    extra_urls: List[AnyHttpUrl] = []
    careers_overrides: List[AnyHttpUrl] = []
    respect_robots: bool = True
    include_feeds: bool = False
    timeout_sec: int = 10
    return_evidence: bool = True

    company_linkedin: Optional[AnyHttpUrl] = None
    company_name: Optional[str] = None

    # --- Validators ---
    @field_validator("domains", mode="before")
    def validate_domains_input(cls, v, values):
        """Validar que se proporcione domain o domains, pero no ambos"""
        domain = values.data.get('domain') if hasattr(values, 'data') else None
        
        if not domain and not v:
            raise ValueError("Must provide either 'domain' or 'domains'")
        if domain and v:
            raise ValueError("Cannot provide both 'domain' and 'domains'")
        if v and len(v) > 50:  # Aumentado de 20 a 50 dominios
            raise ValueError("Maximum 50 domains allowed")
        if v and len(v) == 0:
            raise ValueError("'domains' cannot be empty")
            
        return v

    @field_validator("company_linkedin", mode="before")
    def empty_str_to_none_url(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v

    @field_validator("company_name", mode="before")
    def empty_str_to_none_name(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v


# -------- Context

class ContextBlock(BaseModel):
    # Simplified context - no bullets for performance
    summary: Optional[str] = None  # Simple text summary instead of bullets


# -------- Tech stack

class TechFingerprint(BaseModel):
    tools: List[str] = []  # List of tools in this category
    evidence: Optional[str] = None


# -------- GTM Intelligence (NEW)

class LinkedInInfo(BaseModel):
    employee_count: Optional[int] = None
    description: Optional[str] = None
    linkedin_industry: Optional[str] = None
    company_size_segment: Optional[str] = None

class GrowthSignals(BaseModel):
    funding_signals: List[str] = []
    growth_mentions: List[str] = []
    partnership_signals: List[str] = []
    product_launches: List[str] = []
    growth_score: float = 0.0
    score_factors: List[str] = []
    priority_level: str = "Low"

class CompanyMaturity(BaseModel):
    level: str = "Unknown"  # Early Startup, Scale-up, Established, Public Company
    indicators: List[str] = []

class SEOMetrics(BaseModel):
    meta_title_length: Optional[int] = None
    meta_description_length: Optional[int] = None
    has_structured_data: bool = False
    has_sitemap_link: bool = False
    page_load_time_ms: Optional[int] = None  # Page load time in milliseconds
    h1_count: Optional[int] = None
    h2_count: Optional[int] = None
    image_alt_missing: Optional[int] = None  # Number of images without alt text
    internal_links_count: Optional[int] = None
    external_links_count: Optional[int] = None
    page_size_kb: Optional[float] = None  # Page size in KB

# -------- Enrichment Data (NEW)

class DomainIntelligence(BaseModel):
    hosting_ip: Optional[str] = None
    hosting_provider: Optional[str] = None
    email_provider: Optional[str] = None
    response_time_ms: Optional[int] = None

class BusinessIntelligence(BaseModel):
    verified_business: Optional[bool] = None
    business_type: Optional[str] = None
    location: Optional[str] = None
    confidence: Optional[str] = None
    response_time_ms: Optional[int] = None

class LocalPresence(BaseModel):
    business_verified: Optional[bool] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    phone_verified: Optional[str] = None
    business_hours: Optional[str] = None
    response_time_ms: Optional[int] = None

class EnrichmentData(BaseModel):
    domain_intelligence: Optional[DomainIntelligence] = None
    business_intelligence: Optional[BusinessIntelligence] = None
    local_presence: Optional[LocalPresence] = None
    enrichment_timing: Optional[Dict[str, Any]] = None

# -------- News (novedades internas del sitio)

class NewsItem(BaseModel):
    title: str
    body: str
    url: AnyHttpUrl

# -------- Output

class ScanResponse(BaseModel):
    # Reorganized order: Domain → Company Name → Context → Social → Industry → Tech → SEO
    domain: str
    company_name: Optional[str] = None
    context: ContextBlock
    social: Dict[str, Any] = {}  # Social networks + emails combined
    industry: Optional[str] = None                
    industry_secondary: Optional[str] = None
    tech_stack: Dict[str, TechFingerprint] = {}  # Category name as key, tools as value
    seo_metrics: Optional[SEOMetrics] = None
    
    # External enrichment data (NEW)
    enrichment: Optional[EnrichmentData] = None
    
    # Optional internal data (shown conditionally)
    pages_crawled: List[str] = []
    recent_news: List[NewsItem] = []  # Only 3 most recent news


class BatchScanResponse(BaseModel):
    """Respuesta para escaneos múltiples"""
    batch_id: str
    total_domains: int
    successful_scans: int
    failed_scans: int
    execution_time: str
    resource_profile: str
    results: Dict[str, Dict[str, Any]]  # domain -> scan result
    performance_stats: Dict[str, Any]


class UnifiedScanResponse(BaseModel):
    """Respuesta unificada que puede ser única o múltiple"""
    scan_type: str  # "single" o "batch"
    single_result: Optional[ScanResponse] = None
    batch_result: Optional[BatchScanResponse] = None
