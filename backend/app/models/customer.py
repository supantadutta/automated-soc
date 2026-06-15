"""Customer (tenant of an MSSP org) and customer context models."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin


class Customer(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    criticality: Mapped[str] = mapped_column(String(32), default="medium")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ai_policy: Mapped["CustomerAIPolicy"] = relationship(
        back_populates="customer", uselist=False
    )


class CustomerAIPolicy(Base, TimestampMixin):
    __tablename__ = "customer_ai_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, unique=True
    )
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False)

    external_ai_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fallback_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    redact_pii_before_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    store_ai_outputs: Mapped[bool] = mapped_column(Boolean, default=True)
    local_only_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped["Customer"] = relationship(back_populates="ai_policy")


class CustomerAllowlist(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "customer_allowlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(48), nullable=False)  # ip|domain|user|hash|hostname
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asset_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # ad|dns|pam|scanner|endpoint
    criticality: Mapped[str] = mapped_column(String(32), default="medium")


class ServiceAccount(Base, TimestampMixin):
    __tablename__ = "service_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)


class KnownFalsePositive(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "known_false_positives"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    alert_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
