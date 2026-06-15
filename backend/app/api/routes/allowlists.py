"""Customer allowlist routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.customer import CustomerAllowlist
from app.schemas import AllowlistCreate, AllowlistOut
from app.services import audit_service

router = APIRouter(prefix="/allowlists", tags=["allowlists"])


@router.get("", response_model=list[AllowlistOut])
def list_allowlists(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
                    customer_id: int | None = None):
    stmt = select(CustomerAllowlist).where(CustomerAllowlist.organization_id == ctx.organization_id)
    if customer_id:
        stmt = stmt.where(CustomerAllowlist.customer_id == customer_id)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=AllowlistOut, status_code=201)
def create_allowlist(payload: AllowlistCreate, db: Session = Depends(get_db),
                     ctx: TenantContext = Depends(require_write)):
    entry = CustomerAllowlist(
        organization_id=ctx.organization_id, customer_id=payload.customer_id,
        entry_type=payload.entry_type, value=payload.value, reason=payload.reason,
        created_by=ctx.user_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit_service.record(db, organization_id=ctx.organization_id, action="allowlist.create",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="allowlist",
                         target_id=entry.id, detail={"value": payload.value})
    return entry


@router.delete("/{allowlist_id}", status_code=204)
def delete_allowlist(allowlist_id: int, db: Session = Depends(get_db),
                     ctx: TenantContext = Depends(require_write)):
    entry = db.get(CustomerAllowlist, allowlist_id)
    if not entry or entry.organization_id != ctx.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Allowlist entry not found")
    db.delete(entry)
    db.commit()
    audit_service.record(db, organization_id=ctx.organization_id, action="allowlist.delete",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="allowlist",
                         target_id=allowlist_id)
    return None
