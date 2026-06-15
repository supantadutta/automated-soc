"""Per-organization runtime AI configuration.

Lets operators override the default provider / routing mode at runtime (audited)
without editing env vars. Stored in ``ai_provider_configs`` using a reserved
``__runtime__`` provider marker so no schema change is required. Falls back to
environment settings when unset.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.router import ROUTING_POLICIES, normalize_mode
from app.core.config import settings
from app.models.ai import AIProviderConfig
from app.services import audit_service

RUNTIME_MARKER = "__runtime__"


def _row(db: Session, organization_id: int) -> AIProviderConfig | None:
    return db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.organization_id == organization_id,
            AIProviderConfig.provider == RUNTIME_MARKER,
        )
    ).scalar_one_or_none()


def get_runtime_config(db: Session, organization_id: int) -> dict:
    row = _row(db, organization_id)
    cfg = (row.settings if row and row.settings else {}) or {}
    return {
        "default_provider": cfg.get("default_provider") or settings.default_ai_provider,
        "routing_mode": normalize_mode(cfg.get("routing_mode") or settings.ai_routing_mode),
        "fallback_enabled": cfg.get("fallback_enabled", settings.ai_enable_fallback),
        "source": "runtime" if row else "env",
        "available_routing_policies": sorted(set(ROUTING_POLICIES.keys())),
    }


def set_runtime_config(
    db: Session,
    organization_id: int,
    *,
    actor_id: int | None = None,
    actor_email: str | None = None,
    default_provider: str | None = None,
    routing_mode: str | None = None,
    fallback_enabled: bool | None = None,
) -> dict:
    row = _row(db, organization_id)
    if row is None:
        row = AIProviderConfig(organization_id=organization_id, provider=RUNTIME_MARKER,
                               settings={}, is_default=True)
        db.add(row)
        db.flush()
    cfg = dict(row.settings or {})
    changes: dict = {}
    if default_provider is not None:
        cfg["default_provider"] = default_provider
        changes["default_provider"] = default_provider
    if routing_mode is not None:
        cfg["routing_mode"] = normalize_mode(routing_mode)
        changes["routing_mode"] = cfg["routing_mode"]
    if fallback_enabled is not None:
        cfg["fallback_enabled"] = fallback_enabled
        changes["fallback_enabled"] = fallback_enabled
    row.settings = cfg
    db.commit()

    # Audit every AI provider/config change (security requirement).
    audit_service.record(
        db, organization_id=organization_id, action="ai.config.update",
        actor_id=actor_id, actor_email=actor_email, target_type="ai_config",
        target_id=row.id, detail=changes,
    )
    return get_runtime_config(db, organization_id)
