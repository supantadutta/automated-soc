"""Report routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.alert import Alert
from app.models.investigation import Investigation, Report
from app.schemas import ReportDetail, ReportOut
from app.services.report_service import generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_report(db: Session, ctx: TenantContext, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if not report or (not ctx.is_platform_admin and report.organization_id != ctx.organization_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return report


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
                 limit: int = 100):
    return db.execute(
        select(Report).where(Report.organization_id == ctx.organization_id)
        .order_by(Report.created_at.desc()).limit(limit)
    ).scalars().all()


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db),
               ctx: TenantContext = Depends(get_context)):
    return _get_report(db, ctx, report_id)


@router.get("/{report_id}/markdown", response_class=PlainTextResponse)
def get_markdown(report_id: int, db: Session = Depends(get_db),
                 ctx: TenantContext = Depends(get_context)):
    return _get_report(db, ctx, report_id).markdown


@router.post("/{report_id}/regenerate", response_model=ReportOut)
def regenerate(report_id: int, db: Session = Depends(get_db),
               ctx: TenantContext = Depends(require_write)):
    report = _get_report(db, ctx, report_id)
    alert = db.get(Alert, report.alert_id)
    investigation = db.get(Investigation, report.investigation_id)
    if not alert or not investigation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Source alert/investigation missing")
    new_report = generate_report(db, alert, investigation, actor_id=ctx.user_id)
    return new_report
