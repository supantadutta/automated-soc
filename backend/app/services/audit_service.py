"""Audit logging — every significant action is recorded (security req #9)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.misc import AuditLog


def record(
    db: Session,
    *,
    organization_id: int,
    action: str,
    actor_id: int | None = None,
    actor_email: str | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    detail: dict[str, Any] | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    log = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    if commit:
        db.commit()
        db.refresh(log)
    return log
