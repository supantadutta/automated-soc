"""AI observability and configuration models."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedByMixin, TimestampMixin


class AIRun(Base, TimestampMixin, CreatedByMixin):
    """One record per AI call for cost/latency/usage observability."""

    __tablename__ = "ai_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alert_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    investigation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False)


class AIProviderConfig(Base, TimestampMixin):
    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AIPromptTemplate(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "ai_prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
