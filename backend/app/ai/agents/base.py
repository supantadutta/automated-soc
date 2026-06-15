"""Base class for SOC AI agents.

Agents are thin, single-responsibility services that build a prompt, call the
AIRouter, and return structured data. They share the router so observability,
fallback and privacy enforcement happen in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.router import AIRouter, CustomerPolicy


@dataclass
class AgentContext:
    organization_id: int
    customer_id: Optional[int] = None
    alert_id: Optional[int] = None
    investigation_id: Optional[int] = None
    created_by: Optional[int] = None
    policy: CustomerPolicy = None  # type: ignore[assignment]
    override_provider: Optional[str] = None
    db: Optional[Session] = None

    def __post_init__(self):
        if self.policy is None:
            self.policy = CustomerPolicy()


class BaseAgent:
    name = "base_agent"

    def __init__(self, router: AIRouter | None = None):
        self.router = router or AIRouter()

    async def _run(self, request, ctx: AgentContext):
        return await self.router.run(
            request,
            policy=ctx.policy,
            override_provider=ctx.override_provider,
            db=ctx.db,
            organization_id=ctx.organization_id,
            customer_id=ctx.customer_id,
            alert_id=ctx.alert_id,
            investigation_id=ctx.investigation_id,
            created_by=ctx.created_by,
        )
