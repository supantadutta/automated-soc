"""Response recommendations and the human-approval workflow.

Recommendations are advisory only. Acting on a high-risk recommendation requires
an explicit, audited approval request and an approver decision — the platform
never auto-executes containment (security requirement #8).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_manager, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.investigation import ApprovalRequest, ResponseRecommendation
from app.schemas import ApprovalDecision
from app.services import audit_service

router = APIRouter(tags=["response"])


@router.get("/investigations/{investigation_id}/recommendations")
def list_recommendations(investigation_id: int, db: Session = Depends(get_db),
                         ctx: TenantContext = Depends(get_context)):
    rows = db.execute(
        select(ResponseRecommendation).where(
            ResponseRecommendation.organization_id == ctx.organization_id,
            ResponseRecommendation.investigation_id == investigation_id,
        )
    ).scalars().all()
    return [
        {"id": r.id, "action": r.action, "priority": r.priority,
         "requires_human_approval": r.requires_human_approval, "reason": r.reason}
        for r in rows
    ]


@router.post("/recommendations/{recommendation_id}/request-approval")
def request_approval(recommendation_id: int, db: Session = Depends(get_db),
                     ctx: TenantContext = Depends(require_write)):
    rec = db.get(ResponseRecommendation, recommendation_id)
    if not rec or rec.organization_id != ctx.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recommendation not found")
    existing = db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.recommendation_id == recommendation_id,
            ApprovalRequest.status == "pending",
        )
    ).scalar_one_or_none()
    if existing:
        return _serialize(existing)
    req = ApprovalRequest(
        organization_id=ctx.organization_id, investigation_id=rec.investigation_id,
        recommendation_id=recommendation_id, action=rec.action, status="pending",
        created_by=ctx.user_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    audit_service.record(db, organization_id=ctx.organization_id, action="approval.request",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="approval",
                         target_id=req.id, detail={"action": rec.action})
    return _serialize(req)


@router.get("/approvals")
def list_approvals(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
                   status_filter: str | None = None):
    stmt = select(ApprovalRequest).where(ApprovalRequest.organization_id == ctx.organization_id)
    if status_filter:
        stmt = stmt.where(ApprovalRequest.status == status_filter)
    rows = db.execute(stmt.order_by(ApprovalRequest.created_at.desc())).scalars().all()
    return [_serialize(r) for r in rows]


@router.post("/approvals/{approval_id}/decision")
def decide(approval_id: int, payload: ApprovalDecision, db: Session = Depends(get_db),
           ctx: TenantContext = Depends(require_manager)):
    """Approve or reject a containment action. Approval records intent only — the
    platform still does not execute the action automatically."""
    req = db.get(ApprovalRequest, approval_id)
    if not req or req.organization_id != ctx.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Approval request not found")
    if payload.decision not in {"approved", "rejected"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "decision must be approved|rejected")
    req.status = payload.decision
    req.approved_by = ctx.user_id
    db.commit()
    audit_service.record(db, organization_id=ctx.organization_id, action=f"approval.{payload.decision}",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="approval",
                         target_id=req.id, detail={"action": req.action, "note": payload.note})
    return _serialize(req)


def _serialize(r: ApprovalRequest) -> dict:
    return {
        "id": r.id, "investigation_id": r.investigation_id, "recommendation_id": r.recommendation_id,
        "action": r.action, "status": r.status, "approved_by": r.approved_by,
        "created_at": r.created_at,
    }
