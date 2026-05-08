"""
AI Lead Scoring API — Production Grade
========================================
Features:
  - API key authentication
  - Rate limiting (30 req/min)
  - Structured logging
  - Model versioning + metadata
  - Background async logging
  - CORS middleware
  - /metrics endpoint
  - Full input validation
"""

import os
import time
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
load_dotenv()

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("lead_scoring_api")

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── API Key Auth ──────────────────────────────────────────────────────────────
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def load_api_keys() -> set:
    api_keys_env = os.getenv("API_KEYS")

    if not api_keys_env:
        raise RuntimeError("API_KEYS environment variable is not set")

    keys = {k.strip() for k in api_keys_env.split(",") if k.strip()}

    if not keys:
        raise RuntimeError("API_KEYS is empty after parsing")

    return keys

VALID_API_KEYS = load_api_keys()


def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    if not api_key:
        logger.warning("Unauthorized request: missing API key")
        raise HTTPException(status_code=401, detail="Missing API key")

    if api_key not in VALID_API_KEYS:
        logger.warning(f"Unauthorized request with invalid key: {api_key}")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


# ── Model Registry ────────────────────────────────────────────────────────────
class ModelRegistry:
    def __init__(self):
        self.model        = None
        self.version      = None
        self.loaded_at    = None
        self.total_scored = 0
        self.tier_counts  = {"hot": 0, "warm": 0, "cold": 0}

    def load(self, path: str = "lead_model.pkl", version: str = "1.0.0"):
        try:
            self.model     = joblib.load(path)
            self.version   = version
            self.loaded_at = datetime.utcnow().isoformat()
            logger.info(f"Model v{version} loaded from {path}")
        except FileNotFoundError:
            logger.error(f"Model file not found: {path}")
            self.model = None

    def is_ready(self) -> bool:
        return self.model is not None

    def record_prediction(self, tier: str):
        self.total_scored += 1
        self.tier_counts[tier] = self.tier_counts.get(tier, 0) + 1


registry = ModelRegistry()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Lead Scoring API...")
    registry.load(path="lead_model.pkl", version="1.0.0")
    if registry.is_ready():
        logger.info("API ready to serve predictions.")
    else:
        logger.warning("API started without a loaded model.")
    yield
    logger.info("Shutting down AI Lead Scoring API.")


# ── App Init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "AI Lead Scoring API",
    description = "Production-grade ML API for real-time B2B lead qualification.",
    version     = "1.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request Timing Middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start    = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration)
    return response


# ── Schemas ───────────────────────────────────────────────────────────────────
VALID_INDUSTRIES = [
    "SaaS", "Fintech", "Marketing", "E-Commerce", "Consulting",
    "Logistics", "Healthcare", "Education", "HR", "Tech", "Other"
]

class LeadInput(BaseModel):
    name:         str           = Field(..., min_length=2,  max_length=100, example="Jane Doe")
    email:        EmailStr      = Field(...,                                 example="jane@acmecorp.com")
    company:      str           = Field(..., min_length=1,  max_length=150, example="Acme Corp")
    job_title:    str           = Field(..., min_length=2,  max_length=100, example="VP of Operations")
    industry:     str           = Field(...,                                 example="SaaS")
    company_size: int           = Field(..., ge=0, le=3,    description="0=1-10, 1=11-50, 2=51-200, 3=200+")
    budget_flag:  int           = Field(..., ge=0, le=1,    description="1 if budget was mentioned")
    timeline:     int           = Field(..., ge=0, le=2,    description="0=none, 1=3-6mo, 2=immediate")
    pain_points:  int           = Field(..., ge=0, le=4,    description="Number of pain points described")
    message:      Optional[str] = Field(None, max_length=2000, example="We struggle with manual reporting...")

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v):
        if v not in VALID_INDUSTRIES:
            raise ValueError(f"Industry must be one of: {', '.join(VALID_INDUSTRIES)}")
        return v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v):
        return v.lower().strip()

    @field_validator("name", "company", "job_title")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip()


class LeadScore(BaseModel):
    request_id:     str
    timestamp:      str
    name:           str
    email:          str
    company:        str
    job_title:      str
    industry:       str
    score:          int
    tier:           str
    tier_code:      int
    routing_action: str
    confidence:     float
    model_version:  str
    features_used:  dict


class HealthResponse(BaseModel):
    status:        str
    model_loaded:  bool
    model_version: Optional[str]
    loaded_at:     Optional[str]
    uptime_info:   str


class MetricsResponse(BaseModel):
    total_scored:   int
    tier_breakdown: dict
    model_version:  Optional[str]


# ── Feature Engineering ───────────────────────────────────────────────────────
TIER_MAP    = {0: "cold", 1: "warm", 2: "hot"}
ROUTING_MAP = {
    "hot":  "immediate_outreach",
    "warm": "nurture_sequence",
    "cold": "archive_and_monitor"
}

HIGH_FIT_INDUSTRIES = {
    "saas", "fintech", "marketing", "e-commerce",
    "consulting", "logistics", "healthcare", "education", "hr", "tech"
}

SENIORITY_MAP = {
    3: ["ceo", "cto", "coo", "cfo", "vp", "president", "founder", "owner", "partner"],
    2: ["director", "head of", "principal", "chief"],
    1: ["manager", "lead", "senior", "sr.", "sr "]
}

FEATURE_COLUMNS = [
    "job_seniority", "company_size", "budget_flag",
    "timeline", "pain_points", "industry_fit"
]

def extract_seniority(title: str) -> int:
    t = title.lower()
    for level, keywords in sorted(SENIORITY_MAP.items(), reverse=True):
        if any(k in t for k in keywords):
            return level
    return 0

def extract_industry_fit(industry: str) -> int:
    return 1 if industry.lower() in HIGH_FIT_INDUSTRIES else 0

def compute_score(features: list) -> int:
    job_sen, comp_size, budget, timeline, pain, ind_fit = features
    raw = (
        job_sen   * 20 +
        comp_size * 15 +
        budget    * 25 +
        timeline  * 15 +
        pain      *  5 +
        ind_fit   * 10
    )
    return round((raw / 190) * 100)


# ── Background Logging ────────────────────────────────────────────────────────
def log_prediction(request_id: str, lead_name: str, tier: str,
                   score: int, confidence: float):
    logger.info(
        f"PREDICTION | id={request_id} | lead={lead_name} | "
        f"tier={tier} | score={score} | confidence={confidence}"
    )


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "service": "AI Lead Scoring API",
        "version": "1.0.0",
        "status":  "live",
        "docs":    "/docs",
        "health":  "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    try:
        ready = registry.is_ready()
        
        return HealthResponse(
            status="ok" if ready else "degraded",
            model_loaded=ready,
            model_version=getattr(registry, "version", "unknown"),
            loaded_at=getattr(registry, "loaded_at", None),
            uptime_info=f"Serving since {getattr(registry, 'loaded_at', 'unknown')}"
        )

    except Exception as e:
        return HealthResponse(
            status="degraded",
            model_loaded=False,
            model_version="unknown",
            loaded_at=None,
            uptime_info=f"Health check error: {str(e)}"
        )


@app.get("/metrics", response_model=MetricsResponse, tags=["System"],
         dependencies=[Depends(verify_api_key)])
def metrics():
    return MetricsResponse(
        total_scored   = registry.total_scored,
        tier_breakdown = registry.tier_counts,
        model_version  = registry.version
    )


@app.post("/score-lead", response_model=LeadScore, tags=["Scoring"],
          dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def score_lead(
    request:          Request,
    lead:             LeadInput,
    background_tasks: BackgroundTasks
):
    if not registry.is_ready():
        raise HTTPException(status_code=503,
            detail="Model not available. Try again shortly.")

    request_id = str(uuid.uuid4())[:8]
    timestamp  = datetime.utcnow().isoformat() + "Z"

    seniority = extract_seniority(lead.job_title)
    ind_fit   = extract_industry_fit(lead.industry)

    features = [
        seniority,
        lead.company_size,
        lead.budget_flag,
        lead.timeline,
        lead.pain_points,
        ind_fit
    ]
    features_dict = dict(zip(FEATURE_COLUMNS, features))

    X         = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    tier_code = int(registry.model.predict(X)[0])
    proba     = registry.model.predict_proba(X)[0]
    confidence = round(float(proba[tier_code]), 3)
    tier       = TIER_MAP[tier_code]
    score      = compute_score(features)

    registry.record_prediction(tier)

    background_tasks.add_task(
        log_prediction, request_id, lead.name, tier, score, confidence
    )

    return LeadScore(
        request_id     = request_id,
        timestamp      = timestamp,
        name           = lead.name,
        email          = lead.email,
        company        = lead.company,
        job_title      = lead.job_title,
        industry       = lead.industry,
        score          = score,
        tier           = tier,
        tier_code      = tier_code,
        routing_action = ROUTING_MAP[tier],
        confidence     = confidence,
        model_version  = registry.version,
        features_used  = features_dict
    )