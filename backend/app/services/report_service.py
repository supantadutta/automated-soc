"""Report service: render and persist markdown SOC reports + email/ticket drafts."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents import ReportWriterAgent
from app.models.alert import STATUS_REPORTED, Alert, NormalizedAlert
from app.models.investigation import EmailDraft, Investigation, Report, TicketNote
from app.services.correlation_service import correlate_alert
from app.services.parser_service import normalized_to_dict


def generate_report(db: Session, alert: Alert, investigation: Investigation,
                    actor_id: int | None = None) -> Report:
    normalized = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    norm_dict = normalized_to_dict(normalized) if normalized else {}

    correlation = correlate_alert(db, alert, normalized) if normalized else {"matches": []}
    result = investigation.result or {}
    result.setdefault("_provider", investigation.provider or "mock")
    result.setdefault("_model", investigation.model or "mock-soc-1")

    alert_dict = {
        "title": alert.title, "source_tool": alert.source_tool,
        "severity": alert.severity, "category": alert.category,
    }
    markdown = ReportWriterAgent().render_markdown(alert_dict, norm_dict, result, correlation)

    report = Report(
        organization_id=alert.organization_id, customer_id=alert.customer_id, alert_id=alert.id,
        investigation_id=investigation.id, title=f"SOC Report — {alert.title}", markdown=markdown,
        verdict=investigation.verdict, confidence_score=investigation.confidence_score,
        created_by=actor_id,
    )
    db.add(report)

    if result.get("customer_email_draft"):
        db.add(EmailDraft(
            organization_id=alert.organization_id, alert_id=alert.id,
            investigation_id=investigation.id, subject=f"SOC Notification — {alert.title}",
            body=result["customer_email_draft"],
        ))
    if result.get("ticket_update"):
        db.add(TicketNote(
            organization_id=alert.organization_id, alert_id=alert.id,
            investigation_id=investigation.id, body=result["ticket_update"],
        ))

    alert.status = STATUS_REPORTED
    db.commit()
    db.refresh(report)
    return report
