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

    # Pull prior verdicts/feedback for correlated alerts.
    correlated_alert_ids = list({m["alert_id"] for m in deduped})
    prior_verdicts: list[str] = []
    if correlated_alert_ids:
        invs = db.execute(
            select(Investigation).where(
                Investigation.organization_id == org,
                Investigation.alert_id.in_(correlated_alert_ids),
            )
        ).scalars().all()
        prior_verdicts = [i.verdict for i in invs if i.verdict]

    alert.status = STATUS_CORRELATED
    db.commit()

    return {
        "matches": deduped,
        "correlation_count": len(deduped),
        "prior_verdicts": prior_verdicts,
        "correlated_alert_ids": correlated_alert_ids,
    }
