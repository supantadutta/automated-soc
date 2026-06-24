"""Correlation service: find related prior alerts and analyst feedback signals."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import STATUS_CORRELATED, Alert, NormalizedAlert
from app.models.investigation import Feedback, Investigation


def correlate_alert(db: Session, alert: Alert, normalized: NormalizedAlert) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    org = alert.organization_id

    def find(field, value, reason):
        if not value:
            return
        rows = db.execute(
            select(NormalizedAlert)
            .where(
                NormalizedAlert.organization_id == org,
                field == value,
                NormalizedAlert.alert_id != alert.id,
            )
            .limit(10)
        ).scalars().all()
        for r in rows:
            matches.append({"alert_id": r.alert_id, "reason": reason, "value": value})

    find(NormalizedAlert.src_ip, normalized.src_ip, "Same source IP")
    find(NormalizedAlert.dest_ip, normalized.dest_ip, "Same destination IP")
    find(NormalizedAlert.username, normalized.username, "Same username")
    find(NormalizedAlert.hostname, normalized.hostname, "Same hostname")
    find(NormalizedAlert.alert_name, normalized.alert_name, "Same alert name")

    # Deduplicate by (alert_id, reason).
    seen = set()
    deduped = []
    for m in matches:
        key = (m["alert_id"], m["reason"])
        if key not in seen:
            seen.add(key)
            deduped.append(m)

    # Pull prior verdicts and analyst feedback for correlated alerts so the
    # feedback loop actually influences future investigations.
    correlated_alert_ids = list({m["alert_id"] for m in deduped})
    prior_verdicts: list[str] = []
    feedback_summary: dict[str, int] = {}
    if correlated_alert_ids:
        invs = db.execute(
            select(Investigation).where(
                Investigation.organization_id == org,
                Investigation.alert_id.in_(correlated_alert_ids),
            )
        ).scalars().all()
        prior_verdicts = [i.verdict for i in invs if i.verdict]

        inv_ids = [i.id for i in invs]
        if inv_ids:
            fbs = db.execute(
                select(Feedback).where(
                    Feedback.organization_id == org,
                    Feedback.investigation_id.in_(inv_ids),
                )
            ).scalars().all()
            for fb in fbs:
                feedback_summary[fb.label] = feedback_summary.get(fb.label, 0) + 1

    signal = _feedback_signal(feedback_summary)

    alert.status = STATUS_CORRELATED
    db.commit()

    return {
        "matches": deduped,
        "correlation_count": len(deduped),
        "prior_verdicts": prior_verdicts,
        "correlated_alert_ids": correlated_alert_ids,
        "feedback_summary": feedback_summary,
        "feedback_signal": signal,
    }


# Labels that lean benign vs malicious for the feedback-influenced confidence.
_BENIGN_LABELS = {"FP", "Benign", "Duplicate"}
_MALICIOUS_LABELS = {"TP", "Escalated", "Customer Confirmed"}


def _feedback_signal(summary: dict[str, int]) -> str:
    """Aggregate analyst feedback on correlated alerts into a directional signal."""
    if not summary:
        return "none"
    benign = sum(v for k, v in summary.items() if k in _BENIGN_LABELS)
    malicious = sum(v for k, v in summary.items() if k in _MALICIOUS_LABELS)
    if benign > malicious:
        return "benign_leaning"
    if malicious > benign:
        return "malicious_leaning"
    return "mixed"
