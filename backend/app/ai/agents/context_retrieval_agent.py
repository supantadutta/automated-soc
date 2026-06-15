"""Context Retrieval Agent — pulls customer SOPs, prior similar alerts,
allowlist matches and analyst feedback from the database and vector memory."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import CustomerAllowlist, KnownFalsePositive
from app.models.misc import KnowledgeDocument


class ContextRetrievalAgent:
    name = "context_retrieval_agent"

    def gather(
        self,
        db: Session,
        organization_id: int,
        customer_id: int | None,
        normalized: dict[str, Any],
    ) -> dict[str, Any]:
        allowlist_hits: list[str] = []
        if customer_id:
            entries = db.execute(
                select(CustomerAllowlist).where(
                    CustomerAllowlist.organization_id == organization_id,
                    CustomerAllowlist.customer_id == customer_id,
                )
            ).scalars().all()
            indicator_values = {
                str(normalized.get(k))
                for k in ["src_ip", "dest_ip", "username", "hostname", "domain", "file_hash"]
                if normalized.get(k)
            }
            for entry in entries:
                if entry.value in indicator_values:
                    allowlist_hits.append(f"{entry.entry_type}:{entry.value} ({entry.reason or 'allowlisted'})")

        prior_fp = False
        if customer_id and normalized.get("alert_name"):
            fps = db.execute(
                select(KnownFalsePositive).where(
                    KnownFalsePositive.organization_id == organization_id,
                    KnownFalsePositive.customer_id == customer_id,
                )
            ).scalars().all()
            for fp in fps:
                if fp.alert_name and fp.alert_name.lower() in (normalized.get("alert_name") or "").lower():
                    prior_fp = True

        sops = []
        if customer_id:
            docs = db.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.organization_id == organization_id,
                    KnowledgeDocument.customer_id == customer_id,
                ).limit(5)
            ).scalars().all()
            sops = [{"title": d.title, "excerpt": d.content[:200]} for d in docs]

        return {
            "allowlist_hits": allowlist_hits,
            "allowlisted": bool(allowlist_hits),
            "prior_false_positive": prior_fp,
            "customer_sops": sops,
        }
