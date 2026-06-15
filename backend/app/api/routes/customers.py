"""Customer and customer AI-policy routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.customer import Customer, CustomerAIPolicy
from app.schemas import (
    AIPolicyOut,
    AIPolicyUpdate,
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
)
from app.services import audit_service

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_customer(db: Session, ctx: TenantContext, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer or (not ctx.is_platform_admin and customer.organization_id != ctx.organization_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    rows = db.execute(
        select(Customer).where(Customer.organization_id == ctx.organization_id)
    ).scalars().all()
    return rows


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db),
                    ctx: TenantContext = Depends(require_write)):
    customer = Customer(organization_id=ctx.organization_id, created_by=ctx.user_id,
                        **payload.model_dump())
    db.add(customer)
    db.flush()
    # Default AI policy.
    db.add(CustomerAIPolicy(customer_id=customer.id, organization_id=ctx.organization_id))
    db.commit()
    db.refresh(customer)
    audit_service.record(db, organization_id=ctx.organization_id, action="customer.create",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="customer",
                         target_id=customer.id)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db),
                 ctx: TenantContext = Depends(get_context)):
    return _get_customer(db, ctx, customer_id)


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db),
                    ctx: TenantContext = Depends(require_write)):
    customer = _get_customer(db, ctx, customer_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(customer, k, v)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}/ai-policy", response_model=AIPolicyOut)
def get_ai_policy(customer_id: int, db: Session = Depends(get_db),
                  ctx: TenantContext = Depends(get_context)):
    _get_customer(db, ctx, customer_id)
    policy = db.execute(
        select(CustomerAIPolicy).where(CustomerAIPolicy.customer_id == customer_id)
    ).scalar_one_or_none()
    if not policy:
        policy = CustomerAIPolicy(customer_id=customer_id, organization_id=ctx.organization_id)
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


@router.put("/{customer_id}/ai-policy", response_model=AIPolicyOut)
def update_ai_policy(customer_id: int, payload: AIPolicyUpdate, db: Session = Depends(get_db),
                     ctx: TenantContext = Depends(require_write)):
    _get_customer(db, ctx, customer_id)
    policy = db.execute(
        select(CustomerAIPolicy).where(CustomerAIPolicy.customer_id == customer_id)
    ).scalar_one_or_none()
    if not policy:
        policy = CustomerAIPolicy(customer_id=customer_id, organization_id=ctx.organization_id)
        db.add(policy)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)
    db.commit()
    db.refresh(policy)
    audit_service.record(db, organization_id=ctx.organization_id, action="customer.ai_policy.update",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="customer",
                         target_id=customer_id, detail=payload.model_dump(exclude_unset=True))
    return policy
