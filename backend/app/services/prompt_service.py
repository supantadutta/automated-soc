"""Prompt template management with versioning.

Prompts live in code (``app.ai.prompts``) as the source of truth and are also
mirrored into the database so operators can create new versions, activate/
deactivate them, and (placeholder) evaluate them — without redeploying.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.prompts import SYSTEM_PROMPTS
from app.models.ai import AIPromptTemplate
from app.services import audit_service

PROMPT_TYPES = list(SYSTEM_PROMPTS.keys())


def seed_default_prompts(db: Session, organization_id: int) -> None:
    for ptype, template in SYSTEM_PROMPTS.items():
        exists = db.execute(
            select(AIPromptTemplate).where(
                AIPromptTemplate.organization_id == organization_id,
                AIPromptTemplate.prompt_type == ptype,
            )
        ).first()
        if not exists:
            db.add(AIPromptTemplate(
                organization_id=organization_id, prompt_type=ptype,
                name=f"{ptype} (default)", template=template, version=1, is_active=True,
            ))
    db.commit()


def list_prompts(db: Session, organization_id: int) -> list[dict]:
    rows = db.execute(
        select(AIPromptTemplate).where(AIPromptTemplate.organization_id == organization_id)
        .order_by(AIPromptTemplate.prompt_type, AIPromptTemplate.version.desc())
    ).scalars().all()
    return [_serialize(r) for r in rows]


def create_version(db: Session, organization_id: int, prompt_type: str, template: str,
                   name: str | None = None, actor_id: int | None = None,
                   actor_email: str | None = None) -> dict:
    latest = db.execute(
        select(AIPromptTemplate).where(
            AIPromptTemplate.organization_id == organization_id,
            AIPromptTemplate.prompt_type == prompt_type,
        ).order_by(AIPromptTemplate.version.desc())
    ).scalars().first()
    new_version = (latest.version + 1) if latest else 1
    # Deactivate previous active versions of this type.
    for row in db.execute(select(AIPromptTemplate).where(
        AIPromptTemplate.organization_id == organization_id,
        AIPromptTemplate.prompt_type == prompt_type,
    )).scalars().all():
        row.is_active = False
    created = AIPromptTemplate(
        organization_id=organization_id, prompt_type=prompt_type,
        name=name or f"{prompt_type} v{new_version}", template=template,
        version=new_version, is_active=True, created_by=actor_id,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    audit_service.record(db, organization_id=organization_id, action="ai.prompt.create_version",
                         actor_id=actor_id, actor_email=actor_email, target_type="prompt",
                         target_id=created.id, detail={"prompt_type": prompt_type, "version": new_version})
    return _serialize(created)


def activate(db: Session, organization_id: int, prompt_id: int, actor_id: int | None = None,
             actor_email: str | None = None) -> dict | None:
    target = db.get(AIPromptTemplate, prompt_id)
    if not target or target.organization_id != organization_id:
        return None
    for row in db.execute(select(AIPromptTemplate).where(
        AIPromptTemplate.organization_id == organization_id,
        AIPromptTemplate.prompt_type == target.prompt_type,
    )).scalars().all():
        row.is_active = row.id == prompt_id
    db.commit()
    audit_service.record(db, organization_id=organization_id, action="ai.prompt.activate",
                         actor_id=actor_id, actor_email=actor_email, target_type="prompt",
                         target_id=prompt_id, detail={"prompt_type": target.prompt_type, "version": target.version})
    return _serialize(target)


def evaluate(db: Session, organization_id: int, prompt_id: int) -> dict:
    """Placeholder prompt evaluation: heuristic score over guardrail coverage."""
    target = db.get(AIPromptTemplate, prompt_id)
    if not target or target.organization_id != organization_id:
        return {"error": "not found"}
    t = (target.template or "").lower()
    checks = {
        "mentions_evidence": "evidence" in t,
        "mentions_json": "json" in t,
        "mentions_confidence": "confidence" in t,
        "mentions_human_approval": "human" in t or "approval" in t,
        "forbids_destructive": "destructive" in t or "never" in t,
    }
    score = round(100 * sum(checks.values()) / len(checks), 1)
    return {"prompt_id": prompt_id, "score": score, "checks": checks,
            "note": "Heuristic placeholder. Wire a real eval set for production scoring."}


def _serialize(r: AIPromptTemplate) -> dict:
    return {
        "id": r.id, "prompt_type": r.prompt_type, "name": r.name, "version": r.version,
        "is_active": r.is_active, "template": r.template,
        "last_modified": (r.updated_at or datetime.now(timezone.utc)).isoformat(),
    }
