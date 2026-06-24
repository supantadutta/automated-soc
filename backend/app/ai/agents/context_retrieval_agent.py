"""Context Retrieval Agent — pulls customer SOPs, prior similar alerts,
allowlist matches and analyst feedback from the database and vector memory."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.memory import memory
from app.models.customer import CustomerAllowlist, KnownFalsePositive


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

        # Semantic retrieval from vector memory: relevant SOPs and similar past
        # investigations (the RAG layer).
        query = " ".join(str(normalized.get(k)) for k in
                         ["alert_name", "src_ip", "username", "hostname", "domain"]
                         if normalized.get(k))
        sops = [
            {"title": (h.meta or {}).get("title", "SOP"), "excerpt": h.text[:240], "score": h.score}
            for h in memory.search(db, organization_id=organization_id, query=query, k=4,
                                   customer_id=customer_id, source_types=["sop"])
        ]
        similar_cases = [
            {"summary": h.text[:240], "verdict": (h.meta or {}).get("verdict"),
             "alert_id": (h.meta or {}).get("alert_id"), "score": h.score}
            for h in memory.search(db, organization_id=organization_id, query=query, k=4,
                                   source_types=["investigation"])
        ]

        return {
            "allowlist_hits": allowlist_hits,
            "allowlisted": bool(allowlist_hits),
            "prior_false_positive": prior_fp,
            "customer_sops": sops,
            "similar_cases": similar_cases,
        }
