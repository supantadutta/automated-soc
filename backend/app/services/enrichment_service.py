"""Enrichment service: enrich an alert's IOCs via mock + configured providers."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment import EXTERNAL_PROVIDERS, MockEnrichmentProvider
from app.models.alert import STATUS_ENRICHED, Alert, EnrichmentResult, IOC

_mock = MockEnrichmentProvider()


async def enrich_alert(db: Session, alert: Alert) -> dict[str, list[dict[str, Any]]]:
    iocs = db.execute(select(IOC).where(IOC.alert_id == alert.id)).scalars().all()
    by_ioc: dict[str, list[dict[str, Any]]] = {}

    # Clear prior results for idempotency.
    ioc_ids = [i.id for i in iocs]
    if ioc_ids:
        db.query(EnrichmentResult).filter(EnrichmentResult.ioc_id.in_(ioc_ids)).delete(
            synchronize_session=False
        )

    providers = [_mock] + EXTERNAL_PROVIDERS
    for ioc in iocs:
        results: list[dict[str, Any]] = []
        max_risk = 0
        worst = "unknown"
        for provider in providers:
            if not provider.supports(ioc.ioc_type):
                continue
            data = await provider.enrich(ioc.ioc_type, ioc.value)
            # Skip unconfigured external providers that return nothing useful.
            if provider.name != "mock" and data.verdict == "unknown" and data.risk_score == 0:
                continue
            db.add(EnrichmentResult(
                ioc_id=ioc.id, organization_id=alert.organization_id, provider=data.provider,
                verdict=data.verdict, risk_score=data.risk_score, summary=data.summary, raw=data.raw,
            ))
            results.append({
                "provider": data.provider, "ioc_type": ioc.ioc_type, "verdict": data.verdict,
                "risk_score": data.risk_score, "summary": data.summary,
            })
            if data.risk_score > max_risk:
                max_risk = data.risk_score
            if data.verdict == "malicious":
                worst = "malicious"
            elif data.verdict == "suspicious" and worst != "malicious":
                worst = "suspicious"
            elif data.verdict == "clean" and worst == "unknown":
                worst = "clean"

        ioc.risk_score = max_risk
        ioc.reputation = worst
        by_ioc[ioc.value] = results

    alert.status = STATUS_ENRICHED
    db.commit()
    return by_ioc
