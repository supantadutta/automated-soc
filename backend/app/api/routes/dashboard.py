"""Dashboard aggregation routes."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context
from app.core.config import settings
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.ai import AIRun
from app.models.alert import Alert
from app.models.investigation import Investigation

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    org = ctx.organization_id
    alerts = db.execute(select(Alert).where(Alert.organization_id == org)).scalars().all()
    invs = db.execute(select(Investigation).where(Investigation.organization_id == org)).scalars().all()

    severity_counts = Counter(a.severity for a in alerts)
    status_counts = Counter(a.status for a in alerts)
    verdict_counts = Counter(i.verdict for i in invs if i.verdict)
    category_counts = Counter(a.category for a in alerts if a.category)

    open_alerts = sum(1 for a in alerts if a.status not in {"reported", "closed"})
    needs_review = sum(1 for i in invs if i.verdict == "Needs Review")

    return {
        "total_alerts": len(alerts),
        "open_alerts": open_alerts,
        "total_investigations": len(invs),
        "needs_review": needs_review,
        "severity_breakdown": dict(severity_counts),
        "status_breakdown": dict(status_counts),
        "verdict_distribution": dict(verdict_counts),
        "top_categories": dict(category_counts.most_common(8)),
    }


@router.get("/daily-summary")
def daily_summary(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    org = ctx.organization_id
    since = datetime.now(timezone.utc) - timedelta(days=1)
    alerts = db.execute(
        select(Alert).where(Alert.organization_id == org, Alert.created_at >= since)
    ).scalars().all()
    invs = db.execute(
        select(Investigation).where(Investigation.organization_id == org, Investigation.created_at >= since)
    ).scalars().all()
    verdicts = Counter(i.verdict for i in invs if i.verdict)
    tp = verdicts.get("True Positive", 0)
    fp = verdicts.get("False Positive", 0) + verdicts.get("Benign Authorized Activity", 0)
    nr = verdicts.get("Needs Review", 0)
    narrative = (
        f"In the last 24h the SOC ingested {len(alerts)} alerts and completed "
        f"{len(invs)} investigations: {tp} true positive(s), {fp} benign/false positive(s), "
        f"and {nr} requiring further review. All response actions remain human-approved."
    )
    return {
        "window": "24h", "alerts": len(alerts), "investigations": len(invs),
        "verdicts": dict(verdicts), "narrative": narrative,
        "highlights": [
            {"alert_id": a.id, "title": a.title, "severity": a.severity, "verdict": a.ai_verdict}
            for a in sorted(alerts, key=lambda x: x.created_at, reverse=True)[:10]
        ],
    }


@router.get("/mitre-summary")
def mitre_summary(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    invs = db.execute(
        select(Investigation).where(Investigation.organization_id == ctx.organization_id)
    ).scalars().all()
    tactic_counts: Counter = Counter()
    technique_counts: Counter = Counter()
    for inv in invs:
        for m in (inv.result or {}).get("mitre_mapping", []) or []:
            if m.get("tactic"):
                tactic_counts[m["tactic"]] += 1
            label = f"{m.get('technique_id','')} {m.get('technique','')}".strip()
            if label:
                technique_counts[label] += 1
    return {
        "tactics": dict(tactic_counts),
        "techniques": dict(technique_counts.most_common(15)),
    }


@router.get("/ai-operations")
def ai_operations(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    runs = db.execute(
        select(AIRun).where(AIRun.organization_id == ctx.organization_id)
        .order_by(AIRun.created_at.desc())
    ).scalars().all()
    total = len(runs)
    local = sum(1 for r in runs if r.is_local)
    by_provider: Counter = Counter(r.provider for r in runs)
    return {
        "active_provider": settings.default_ai_provider,
        "routing_mode": settings.ai_routing_mode,
        "fallback_chain": settings.fallback_chain_list,
        "total_runs": total,
        "failed": sum(1 for r in runs if not r.success),
        "fallback_used": sum(1 for r in runs if r.fallback_used),
        "local_requests": local,
        "cloud_requests": total - local,
        "estimated_cost": round(sum(r.estimated_cost for r in runs), 4),
        "avg_latency_ms": round(sum(r.latency_ms for r in runs) / total, 1) if total else 0,
        "by_provider": dict(by_provider),
        "recent_runs": [
            {"id": r.id, "provider": r.provider, "model": r.model, "success": r.success,
             "latency_ms": r.latency_ms, "estimated_cost": r.estimated_cost,
             "fallback_used": r.fallback_used, "is_local": r.is_local, "created_at": r.created_at}
            for r in runs[:20]
        ],
    }
