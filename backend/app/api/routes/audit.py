"""Audit log routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.misc import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
                    limit: int = 200, action: str | None = None):
    stmt = select(AuditLog).where(AuditLog.organization_id == ctx.organization_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": r.id, "action": r.action, "actor_email": r.actor_email,
            "target_type": r.target_type, "target_id": r.target_id, "detail": r.detail,
            "created_at": r.created_at,
        }
        for r in rows
    ]
