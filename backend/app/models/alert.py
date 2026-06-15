"""Alert ingestion, normalization, entity and IOC models."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin

# Alert lifecycle status
STATUS_NEW = "new"
STATUS_PARSED = "parsed"
STATUS_ENRICHED = "enriched"
STATUS_CORRELATED = "correlated"
STATUS_INVESTIGATED = "investigated"
STATUS_REPORTED = "reported"
STATUS_CLOSED = "closed"


class Alert(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_tool: Mapped[str | None] = mapped_column(String(120), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="Medium")
    status: Mapped[str] = mapped_column(String(32), default=STATUS_NEW, index=True)
    ingest_method: Mapped[str] = mapped_column(String(48), default="manual")  # manual|json|webhook|csv|email

    raw_format: Mapped[str] = mapped_column(String(24), default="text")  # text|json|csv
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)

    normalized: Mapped["NormalizedAlert | None"] = relationship(
        back_populates="alert", uselist=False
    )
    entities: Mapped[list["Entity"]] = relationship(back_populates="alert")
    iocs: Mapped[list["IOC"]] = relationship(back_populates="alert")


class NormalizedAlert(Base, TimestampMixin):
    __tablename__ = "normalized_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False, unique=True)

    alert_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_tool: Mapped[str | None] = mapped_column(String(120), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dest_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    process_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    alert: Mapped["Alert"] = relationship(back_populates="normalized")


class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)

    alert: Mapped["Alert"] = relationship(back_populates="entities")


class IOC(Base, TimestampMixin):
    __tablename__ = "iocs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    ioc_type: Mapped[str] = mapped_column(String(48), nullable=False)  # ip|domain|url|hash|email|hostname|username
    value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    reputation: Mapped[str | None] = mapped_column(String(64), nullable=True)

    alert: Mapped["Alert"] = relationship(back_populates="iocs")
    enrichment: Mapped[list["EnrichmentResult"]] = relationship(back_populates="ioc")


class EnrichmentResult(Base, TimestampMixin):
    __tablename__ = "enrichment_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ioc_id: Mapped[int] = mapped_column(ForeignKey("iocs.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    ioc: Mapped["IOC"] = relationship(back_populates="enrichment")


class Case(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open")
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
