"""Investigation orchestrator.

Coordinates the multi-agent pipeline:
  Context Retrieval -> IOC Enrichment summary -> MITRE baseline -> Investigation
  Agent (AI) -> Verdict rules -> QA review -> Detection Engineer fill-in.
Persists an Investigation row and response recommendations.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents import (
    AgentContext,
    ContextRetrievalAgent,
    DetectionEngineerAgent,
    InvestigationAgent,
    IOCEnrichmentAgent,
    MitreAgent,
    QAReviewAgent,
)
from app.ai.router import AIRouter, CustomerPolicy
from app.core.config import settings
from app.models.alert import STATUS_INVESTIGATED, Alert, EnrichmentResult, IOC, NormalizedAlert
from app.models.customer import CustomerAIPolicy
from app.models.investigation import Investigation, ResponseRecommendation
from app.services.correlation_service import correlate_alert
from app.services.parser_service import normalized_to_dict
from app.services.verdict_service import apply_rules


def _load_policy(db: Session, customer_id: int | None) -> CustomerPolicy:
    if not customer_id:
        return CustomerPolicy()
    policy = db.execute(
        select(CustomerAIPolicy).where(CustomerAIPolicy.customer_id == customer_id)
    ).scalar_one_or_none()
    return CustomerPolicy.from_model(policy)


def _enrichment_by_ioc(db: Session, alert_id: int) -> dict[str, list[dict[str, Any]]]:
    iocs = db.execute(select(IOC).where(IOC.alert_id == alert_id)).scalars().all()
    out: dict[str, list[dict[str, Any]]] = {}
    for ioc in iocs:
        rows = db.execute(
            select(EnrichmentResult).where(EnrichmentResult.ioc_id == ioc.id)
        ).scalars().all()
        out[ioc.value] = [
            {"provider": r.provider, "ioc_type": ioc.ioc_type, "verdict": r.verdict,
             "risk_score": r.risk_score, "summary": r.summary}
            for r in rows
        ]
    return out


async def investigate_alert(
    db: Session,
    alert: Alert,
    *,
    actor_id: int | None = None,
    override_provider: str | None = None,
    routing_mode: str | None = None,
) -> Investigation:
    normalized = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    norm_dict = normalized_to_dict(normalized) if normalized else {}

    policy = _load_policy(db, alert.customer_id)
    router = AIRouter(mode=routing_mode or settings.ai_routing_mode)
    agent_ctx = AgentContext(
        organization_id=alert.organization_id, customer_id=alert.customer_id,
        alert_id=alert.id, created_by=actor_id, policy=policy,
        override_provider=override_provider, db=db,
    )

    # 1. Context retrieval (allowlist, SOPs, known FPs).
    context_info = ContextRetrievalAgent().gather(
        db, alert.organization_id, alert.customer_id, norm_dict
    )

    # 2. IOC enrichment summary.
    enrichment = _enrichment_by_ioc(db, alert.id)
    ioc_agent = IOCEnrichmentAgent()
    ioc_summary = ioc_agent.summarize(enrichment)
    malicious_iocs = ioc_agent.malicious_values(ioc_summary)

    # 3. Correlation.
    correlation = correlate_alert(db, alert, normalized) if normalized else {"matches": [], "correlation_count": 0}

    # 4. MITRE baseline.
    mitre_baseline = MitreAgent().baseline(alert.category)

    # Build the investigation context fed to the AI.
    context = {
        **norm_dict,
        "category": alert.category,
        "source_tool": alert.source_tool,
        "severity": alert.severity,
        "alert_name": (normalized.alert_name if normalized else alert.title),
        "raw_excerpt": (alert.raw_payload or "")[:2000],
        "ioc_summary": ioc_summary,
        "malicious_iocs": malicious_iocs,
        "allowlisted": context_info["allowlisted"],
        "allowlist_hits": context_info["allowlist_hits"],
        "prior_false_positive": context_info["prior_false_positive"],
        "correlation_count": correlation["correlation_count"],
        "customer_sops": context_info["customer_sops"],
        "mitre_baseline": mitre_baseline,
    }

    # 5. Investigation Agent (AI / mock).
    result = await InvestigationAgent(router).investigate(context, agent_ctx)

    # Ensure baseline MITRE and IOC summary present if AI omitted them.
    if not result.get("mitre_mapping"):
        result["mitre_mapping"] = mitre_baseline
    if not result.get("ioc_summary"):
        result["ioc_summary"] = ioc_summary
    if not (result.get("detection_query_suggestions") or {}).get("splunk"):
        result["detection_query_suggestions"] = DetectionEngineerAgent().suggest(norm_dict, alert.category)

    # 6. Verdict rules enforcement.
    result = apply_rules(result, context)

    # 7. QA review (force Needs Review on weak claims).
    use_ai_qa = settings.ai_enable_output_qa and (routing_mode == "soc_critical" or router.mode == "soc_critical")
    result = await QAReviewAgent(router).review(result, agent_ctx, use_ai=use_ai_qa)

    provider = result.pop("_provider", None)
    model = result.pop("_model", None)
    fallback_used = result.pop("_fallback_used", False)
    result.pop("_pii_redacted", None)

    # Persist investigation.
    investigation = Investigation(
        organization_id=alert.organization_id, customer_id=alert.customer_id, alert_id=alert.id,
        verdict=result.get("verdict"), confidence_score=result.get("confidence_score", 0),
        severity_recommendation=result.get("severity_recommendation"), provider=provider, model=model,
        fallback_used=fallback_used, result=result, qa_warnings=result.get("qa_warnings", []),
        created_by=actor_id,
    )
    db.add(investigation)
    db.flush()

    # Persist response recommendations (recommendation-only, human-approved).
    for act in result.get("recommended_actions", []) or []:
        if not isinstance(act, dict):
            continue
        db.add(ResponseRecommendation(
            organization_id=alert.organization_id, investigation_id=investigation.id,
            action=act.get("action", "")[:500], priority=act.get("priority", "medium"),
            requires_human_approval=act.get("requires_human_approval", True),
            reason=act.get("reason"),
        ))

    # Update alert summary fields.
    alert.status = STATUS_INVESTIGATED
    alert.ai_verdict = result.get("verdict")
    alert.ai_confidence = result.get("confidence_score", 0)
    alert.ai_provider = provider
    alert.ai_model = model

    db.commit()
    db.refresh(investigation)
    return investigation
