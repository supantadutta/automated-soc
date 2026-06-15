"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------- Auth
# NOTE: email is a plain string (not EmailStr) so local-first domains such as
# ``admin@autosoc.local`` are accepted. Format is sanity-checked in the route.
class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    organization_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    organization_id: int

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ Customers
class CustomerCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    timezone: str = "UTC"
    criticality: str = "medium"
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    timezone: Optional[str] = None
    criticality: Optional[str] = None
    notes: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    timezone: str
    criticality: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AIPolicyUpdate(BaseModel):
    external_ai_allowed: Optional[bool] = None
    preferred_provider: Optional[str] = None
    fallback_allowed: Optional[bool] = None
    redact_pii_before_ai: Optional[bool] = None
    store_ai_outputs: Optional[bool] = None
    local_only_mode: Optional[bool] = None


class AIPolicyOut(BaseModel):
    customer_id: int
    external_ai_allowed: bool
    preferred_provider: Optional[str] = None
    fallback_allowed: bool
    redact_pii_before_ai: bool
    store_ai_outputs: bool
    local_only_mode: bool

    class Config:
        from_attributes = True


# --------------------------------------------------------------------- Alerts
class AlertCreate(BaseModel):
    title: Optional[str] = None
    raw_payload: str
    source_tool: Optional[str] = None
    severity: str = "Medium"
    customer_id: Optional[int] = None
    ingest_method: str = "manual"


class InvestigateRequest(BaseModel):
    provider: Optional[str] = None  # override provider (e.g. ollama, mock)
    routing_mode: Optional[str] = None
    auto_pipeline: bool = True  # parse+enrich+correlate if not done


class AlertOut(BaseModel):
    id: int
    title: str
    source_tool: Optional[str] = None
    severity: str
    status: str
    category: Optional[str] = None
    customer_id: Optional[int] = None
    ai_verdict: Optional[str] = None
    ai_confidence: Optional[int] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertDetail(AlertOut):
    raw_payload: str
    raw_format: str
    normalized: Optional[dict[str, Any]] = None
    entities: list[dict[str, Any]] = []
    iocs: list[dict[str, Any]] = []


# ------------------------------------------------------------- Investigations
class InvestigationOut(BaseModel):
    id: int
    alert_id: int
    verdict: Optional[str] = None
    confidence_score: int
    severity_recommendation: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    fallback_used: bool
    result: Optional[dict[str, Any]] = None
    qa_warnings: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    label: str  # TP|FP|Benign|Duplicate|Escalated|Customer Confirmed
    comment: Optional[str] = None


# -------------------------------------------------------------------- Reports
class ReportOut(BaseModel):
    id: int
    alert_id: int
    investigation_id: int
    title: str
    verdict: Optional[str] = None
    confidence_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportDetail(ReportOut):
    markdown: str


# ------------------------------------------------------------------ Allowlist
class AllowlistCreate(BaseModel):
    customer_id: int
    entry_type: str
    value: str
    reason: Optional[str] = None


class AllowlistOut(BaseModel):
    id: int
    customer_id: int
    entry_type: str
    value: str
    reason: Optional[str] = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------ AI
class PromptPreviewRequest(BaseModel):
    prompt_type: str = "soc_investigation"
    sample_text: Optional[str] = None


class ProviderTestRequest(BaseModel):
    provider: str
    model: Optional[str] = None
