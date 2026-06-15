"""Playbooks, audit logs, integrations and knowledge/vector metadata."""
from __future__ import annotations

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedByMixin, TimestampMixin


class Playbook(Base, TimestampMixin):
    __tablename__ = "playbooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    triage_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    investigation_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    containment_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    mitre_techniques: Mapped[list | None] = mapped_column(JSON, nullable=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Integration(Base, TimestampMixin):
    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)  # siem|edr|ticketing|enrichment
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class KnowledgeDocument(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(64), default="sop")  # sop|playbook|report_example|note
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class VectorMemoryMetadata(Base, TimestampMixin):
    __tablename__ = "vector_memory_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vector_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
