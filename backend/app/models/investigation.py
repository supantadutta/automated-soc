"""Investigation, verdict, report and feedback models."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin


class Investigation(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)

    verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    severity_recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # Full structured AI output (matches AI investigation JSON schema)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    qa_warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)

    verdicts: Mapped[list["AIVerdict"]] = relationship(back_populates="investigation")
    reports: Mapped[list["Report"]] = relationship(back_populates="investigation")


class AIVerdict(Base, TimestampMixin):
    __tablename__ = "ai_verdicts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id"), nullable=False
    )
    verdict: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    investigation: Mapped["Investigation"] = relationship(back_populates="verdicts")


class Report(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)

    investigation: Mapped["Investigation"] = relationship(back_populates="reports")


class EmailDraft(Base, TimestampMixin):
    __tablename__ = "email_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(Integer, nullable=False)
    investigation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class TicketNote(Base, TimestampMixin):
    __tablename__ = "ticket_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(Integer, nullable=False)
    investigation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class Feedback(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id"), nullable=False
    )
    # TP | FP | Benign | Duplicate | Escalated | Customer Confirmed
    label: Mapped[str] = mapped_column(String(48), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class ResponseRecommendation(Base, TimestampMixin):
    __tablename__ = "response_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    investigation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(512), nullable=False)
    priority: Mapped[str] = mapped_column(String(24), default="medium")
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApprovalRequest(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    investigation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending")  # pending|approved|rejected
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
