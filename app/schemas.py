# app/app/schemas.py
from pydantic import BaseModel, AnyHttpUrl, Field, field_validator
from typing import List, Optional, Dict, Any

# -------- Inputs

class ScanRequest(BaseModel):
    domain: str
    max_pages: int = Field(default=8, ge=1, le=20)
    extra_urls: List[AnyHttpUrl] = []
    careers_overrides: List[AnyHttpUrl] = []
    respect_robots: bool = True
    include_feeds: bool = False
    timeout_sec: int = 10
    return_evidence: bool = True

    company_linkedin: Optional[AnyHttpUrl] = None
    company_name: Optional[str] = None

    # --- Validators ---
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

class ContextBullet(BaseModel):
    """
    Nota: 'bullet' es el campo estándar.
    Permitimos también inicializar con 'text=' gracias al alias para
    ser compatibles con funciones que construyen bullets condensados.
    """
    source_url: Optional[AnyHttpUrl] = None
    bullet: str = Field(alias="text")
    kind: Optional[str] = "generic"  # value_prop | product | about | blog | news | generic

    class Config:
        populate_by_name = True  # permite pasar 'text=' al crear el modelo


class ContextBlock(BaseModel):
    bullets: List[ContextBullet]
    # Removed feeds as it doesn't provide useful information


# -------- Tech stack

class TechFingerprint(BaseModel):
    category: str  # Will show technology category instead of numbers
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

# -------- News (novedades internas del sitio)

class NewsItem(BaseModel):
    title: str
    body: str
    url: AnyHttpUrl

# -------- Output

class ScanResponse(BaseModel):
    # Reorganized order: Domain → Company Name → Context → Social → Industry → Tech → Competitors → SEO
    domain: str
    company_name: Optional[str] = None
    context: ContextBlock
    social: Dict[str, Any] = {}  # Social networks + emails combined
    industry: Optional[str] = None                
    industry_secondary: Optional[str] = None
    tech_stack: List[TechFingerprint] = []  # Changed to have default empty list
    competitors: List[str] = []  # Competitor domains/companies detected
    seo_metrics: Optional[SEOMetrics] = None
    
    # Optional internal data (shown conditionally)
    pages_crawled: List[str] = []
    recent_news: List[NewsItem] = []  # Only 3 most recent news
    contact_pages: List[str] = []
