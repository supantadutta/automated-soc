"""Playbook routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.misc import Playbook

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


def _serialize(p: Playbook) -> dict:
    return {
        "id": p.id, "key": p.key, "name": p.name, "category": p.category,
        "description": p.description, "triage_steps": p.triage_steps,
        "investigation_steps": p.investigation_steps, "containment_steps": p.containment_steps,
        "mitre_techniques": p.mitre_techniques,
    }


@router.get("")
def list_playbooks(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    rows = db.execute(select(Playbook)).scalars().all()
    return [_serialize(p) for p in rows]


@router.get("/{playbook_id}")
def get_playbook(playbook_id: int, db: Session = Depends(get_db),
                 ctx: TenantContext = Depends(get_context)):
    p = db.get(Playbook, playbook_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Playbook not found")
    return _serialize(p)
