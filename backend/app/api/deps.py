"""FastAPI dependencies: DB session, current user and tenant context, RBAC."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def get_context(user: User = Depends(get_current_user)) -> TenantContext:
    return TenantContext(
        user_id=user.id, organization_id=user.organization_id, role=user.role, email=user.email
    )


def require_write(ctx: TenantContext = Depends(get_context)) -> TenantContext:
    if not ctx.can_write():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions (write)")
    return ctx


def require_org_admin(ctx: TenantContext = Depends(get_context)) -> TenantContext:
    if not ctx.can_manage_org():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requires organization admin")
    return ctx
