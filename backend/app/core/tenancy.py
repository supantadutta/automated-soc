"""Multi-tenant helpers.

Every tenant-scoped query must be filtered by organization_id. The
``TenantContext`` is derived from the authenticated user's JWT and used by
repositories/services to enforce isolation so customer data never leaks across
organizations (security requirements #10-#11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TenantContext:
    user_id: int
    organization_id: int
    role: str
    email: str

    @property
    def is_platform_admin(self) -> bool:
        return self.role == "platform_admin"

    def can_write(self) -> bool:
        return self.role in {
            "platform_admin",
            "organization_admin",
            "soc_manager",
            "analyst",
        }

    def can_manage_org(self) -> bool:
        return self.role in {"platform_admin", "organization_admin"}


def scope_filter(query, model, ctx: TenantContext):
    """Apply organization scoping to a SQLAlchemy query unless platform admin."""
    if ctx.is_platform_admin:
        return query
    if hasattr(model, "organization_id"):
        return query.filter(model.organization_id == ctx.organization_id)
    return query
