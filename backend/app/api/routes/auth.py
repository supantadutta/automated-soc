"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import ROLE_ORG_ADMIN, Organization, User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-") or "org"


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    org_name = payload.organization_name or f"{payload.email.split('@')[0]}'s Organization"
    slug = _slugify(org_name)
    # Ensure unique slug.
    if db.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none():
        slug = f"{slug}-{payload.email.split('@')[0]}"
    org = Organization(name=org_name, slug=slug, is_mssp=True)
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id, email=payload.email, full_name=payload.full_name,
        hashed_password=hash_password(payload.password), role=ROLE_ORG_ADMIN, is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.record(db, organization_id=org.id, action="user.register",
                         actor_id=user.id, actor_email=user.email, target_type="user",
                         target_id=user.id)
    token = create_access_token(str(user.id), {"role": user.role, "org": org.id})
    return TokenResponse(access_token=token, role=user.role, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User disabled")
    audit_service.record(db, organization_id=user.organization_id, action="user.login",
                         actor_id=user.id, actor_email=user.email)
    token = create_access_token(str(user.id), {"role": user.role, "org": user.organization_id})
    return TokenResponse(access_token=token, role=user.role, email=user.email)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
