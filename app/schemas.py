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
    feeds: List[str]
    social: Dict[str, str]
    company_name: Optional[str] = None


# -------- Tech stack

class TechFingerprint(BaseModel):
    category: str
    tool: str
    evidence: Optional[str] = None


# -------- Jobs

class JobPosting(BaseModel):
    title: str
    location: Optional[str] = None
    employment_type: Optional[str] = None
    department: Optional[str] = None
    date_posted: Optional[str] = None
    valid_through: Optional[str] = None
    apply_url: Optional[str] = None
    platform_hint: Optional[str] = None
    source_url: AnyHttpUrl


class JobsSignalsSummary(BaseModel):
    hiring_focus: List[str]
    seniority_mix: Dict[str, int]
    functions_count: Dict[str, int]


class JobsUsefulness(BaseModel):
    score: float
    tags: List[str]
    reasons: List[str]
    freshness_days_p50: Optional[int] = None
    velocity: Dict[str, Any] = {}


class JobsBlock(BaseModel):
    postings: List[JobPosting]
    summary: JobsSignalsSummary
    usefulness: JobsUsefulness


# -------- Extras (fuentes de empleo)

class JobSource(BaseModel):
    name: str
    url: str
    fetchable: bool = True

# -------- News (novedades internas del sitio)

class NewsItem(BaseModel):
    title: str
    body: str
    url: AnyHttpUrl

# -------- Output

class ScanResponse(BaseModel):
    domain: str
    pages_crawled: List[str]
    context: ContextBlock
    tech_stack: List[TechFingerprint]
    jobs: Optional[JobsBlock] = None
    job_sources: List[JobSource] = []
    news: List[NewsItem] = []                 
    emails: List[str] = []      
    contact_pages: List[str] = []                       
    industry: Optional[str] = None                
    industry_secondary: Optional[str] = None
    industry_evidence: List[Dict[str, object]] = []  # opcional: guarda el resultado de detectar_industrias(...)
