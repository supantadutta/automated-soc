"""Investigation listing and analyst feedback routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.investigation import Feedback, Investigation
from app.schemas import FeedbackCreate, InvestigationOut
from app.services import audit_service

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("", response_model=list[InvestigationOut])
def list_investigations(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
                        limit: int = 100):
    rows = db.execute(
        select(Investigation).where(Investigation.organization_id == ctx.organization_id)
        .order_by(Investigation.created_at.desc()).limit(limit)
    ).scalars().all()
    return rows


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(investigation_id: int, db: Session = Depends(get_db),
                      ctx: TenantContext = Depends(get_context)):
    inv = db.get(Investigation, investigation_id)
    if not inv or (not ctx.is_platform_admin and inv.organization_id != ctx.organization_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Investigation not found")
    return inv


@router.post("/{investigation_id}/feedback")
def submit_feedback(investigation_id: int, payload: FeedbackCreate, db: Session = Depends(get_db),
                    ctx: TenantContext = Depends(require_write)):
    inv = db.get(Investigation, investigation_id)
    if not inv or (not ctx.is_platform_admin and inv.organization_id != ctx.organization_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Investigation not found")
    fb = Feedback(organization_id=ctx.organization_id, investigation_id=investigation_id,
                  label=payload.label, comment=payload.comment, created_by=ctx.user_id)
    db.add(fb)
    db.commit()
    audit_service.record(db, organization_id=ctx.organization_id, action="investigation.feedback",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="investigation",
                         target_id=investigation_id, detail={"label": payload.label})
    return {"status": "recorded", "label": payload.label}
