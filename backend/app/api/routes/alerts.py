"""Alert ingestion and the parse -> enrich -> correlate -> investigate pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.alert import Alert, Entity, IOC, NormalizedAlert
from app.models.investigation import Investigation
from app.schemas import (
    AlertCreate,
    AlertDetail,
    AlertOut,
    InvestigateRequest,
    InvestigationOut,
    ReportOut,
)
from app.services import audit_service
from app.services.alert_service import create_alert
from app.services.correlation_service import correlate_alert
from app.services.enrichment_service import enrich_alert
from app.services.investigation_service import investigate_alert
from app.services.parser_service import normalized_to_dict, parse_alert
from app.services.report_service import generate_report

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _get_alert(db: Session, ctx: TenantContext, alert_id: int) -> Alert:
    alert = db.get(Alert, alert_id)
    if not alert or (not ctx.is_platform_admin and alert.organization_id != ctx.organization_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return alert


@router.post("", response_model=AlertOut, status_code=201)
def submit_alert(payload: AlertCreate, db: Session = Depends(get_db),
                 ctx: TenantContext = Depends(require_write)):
    alert = create_alert(
        db, organization_id=ctx.organization_id, customer_id=payload.customer_id,
        title=payload.title or "Untitled Alert", raw_payload=payload.raw_payload,
        source_tool=payload.source_tool, severity=payload.severity,
        ingest_method=payload.ingest_method, actor_id=ctx.user_id,
    )
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.create",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="alert",
                         target_id=alert.id)
    return alert


@router.get("", response_model=list[AlertOut])
def list_alerts(
    db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
    status_filter: str | None = Query(None, alias="status"),
    customer_id: int | None = None, limit: int = 100,
):
    stmt = select(Alert).where(Alert.organization_id == ctx.organization_id)
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
    if customer_id:
        stmt = stmt.where(Alert.customer_id == customer_id)
    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(alert_id: int, db: Session = Depends(get_db),
              ctx: TenantContext = Depends(get_context)):
    alert = _get_alert(db, ctx, alert_id)
    normalized = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    entities = db.execute(select(Entity).where(Entity.alert_id == alert.id)).scalars().all()
    iocs = db.execute(select(IOC).where(IOC.alert_id == alert.id)).scalars().all()

    return AlertDetail(
        id=alert.id, title=alert.title, source_tool=alert.source_tool, severity=alert.severity,
        status=alert.status, category=alert.category, customer_id=alert.customer_id,
        ai_verdict=alert.ai_verdict, ai_confidence=alert.ai_confidence,
        ai_provider=alert.ai_provider, ai_model=alert.ai_model, created_at=alert.created_at,
        raw_payload=alert.raw_payload, raw_format=alert.raw_format,
        normalized=normalized_to_dict(normalized) if normalized else None,
        entities=[{"type": e.entity_type, "value": e.value} for e in entities],
        iocs=[{"ioc_type": i.ioc_type, "value": i.value, "risk_score": i.risk_score,
               "reputation": i.reputation} for i in iocs],
    )


@router.post("/{alert_id}/parse", response_model=AlertDetail)
def parse(alert_id: int, db: Session = Depends(get_db),
          ctx: TenantContext = Depends(require_write)):
    alert = _get_alert(db, ctx, alert_id)
    parse_alert(db, alert)
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.parse",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="alert",
                         target_id=alert.id)
    return get_alert(alert_id, db, ctx)


@router.post("/{alert_id}/enrich", response_model=AlertDetail)
async def enrich(alert_id: int, db: Session = Depends(get_db),
                 ctx: TenantContext = Depends(require_write)):
    alert = _get_alert(db, ctx, alert_id)
    if not db.execute(select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)).scalar_one_or_none():
        parse_alert(db, alert)
    await enrich_alert(db, alert)
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.enrich",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="alert",
                         target_id=alert.id)
    return get_alert(alert_id, db, ctx)


@router.post("/{alert_id}/correlate")
def correlate(alert_id: int, db: Session = Depends(get_db),
              ctx: TenantContext = Depends(require_write)):
    alert = _get_alert(db, ctx, alert_id)
    normalized = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    if not normalized:
        normalized = parse_alert(db, alert)
    result = correlate_alert(db, alert, normalized)
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.correlate",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="alert",
                         target_id=alert.id)
    return result


@router.post("/{alert_id}/investigate", response_model=InvestigationOut)
async def investigate(alert_id: int, payload: InvestigateRequest | None = None,
                      db: Session = Depends(get_db), ctx: TenantContext = Depends(require_write)):
    alert = _get_alert(db, ctx, alert_id)
    payload = payload or InvestigateRequest()

    # Default provider / routing mode from the org's runtime AI config.
    from app.services.ai_config_service import get_runtime_config

    runtime = get_runtime_config(db, ctx.organization_id)
    override_provider = payload.provider or (
        runtime["default_provider"] if runtime["source"] == "runtime" else None
    )
    routing_mode = payload.routing_mode or runtime["routing_mode"]

    # Auto-run the upstream pipeline if requested and not yet done.
    normalized = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    if payload.auto_pipeline:
        if not normalized:
            normalized = parse_alert(db, alert)
        if not db.execute(select(IOC).where(IOC.alert_id == alert.id, IOC.risk_score > 0)).first():
            await enrich_alert(db, alert)

    investigation = await investigate_alert(
        db, alert, actor_id=ctx.user_id, override_provider=override_provider,
        routing_mode=routing_mode,
    )
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.investigate",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="investigation",
                         target_id=investigation.id,
                         detail={"verdict": investigation.verdict, "provider": investigation.provider})
    return investigation


@router.post("/{alert_id}/generate-report", response_model=ReportOut)
def generate(alert_id: int, db: Session = Depends(get_db),
             ctx: TenantContext = Depends(require_write)):
    alert = _get_alert(db, ctx, alert_id)
    investigation = db.execute(
        select(Investigation).where(Investigation.alert_id == alert.id)
        .order_by(Investigation.created_at.desc())
    ).scalars().first()
    if not investigation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Investigate the alert before generating a report")
    report = generate_report(db, alert, investigation, actor_id=ctx.user_id)
    audit_service.record(db, organization_id=ctx.organization_id, action="alert.report",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="report",
                         target_id=report.id)
    return report
