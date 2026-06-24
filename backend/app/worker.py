"""Celery worker for asynchronous SOC pipeline tasks.

Tasks run the same services used synchronously by the API, enabling bulk/queued
processing (e.g. webhook bursts) without blocking request threads.
"""
from __future__ import annotations

import asyncio

from celery import Celery

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("worker")

celery_app = Celery(
    "autosoc",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(task_track_started=True, task_time_limit=300)


def _run(coro):
    """Run an async coroutine from a synchronous Celery worker thread.

    Celery worker threads have no running event loop, so we create a fresh one
    per call (``asyncio.get_event_loop`` is deprecated for this and raises in
    worker threads on 3.10+).
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        asyncio.set_event_loop(None)
        loop.close()


@celery_app.task(name="autosoc.process_alert")
def process_alert(alert_id: int) -> dict:
    """Full pipeline: parse -> enrich -> investigate -> report for one alert."""
    from app.db.session import SessionLocal
    from app.models.alert import Alert
    from app.services.enrichment_service import enrich_alert
    from app.services.investigation_service import investigate_alert
    from app.services.parser_service import parse_alert
    from app.services.report_service import generate_report

    db = SessionLocal()
    try:
        alert = db.get(Alert, alert_id)
        if not alert:
            return {"error": "alert not found", "alert_id": alert_id}
        parse_alert(db, alert)
        _run(enrich_alert(db, alert))
        investigation = _run(investigate_alert(db, alert))
        report = generate_report(db, alert, investigation)
        return {"alert_id": alert_id, "verdict": investigation.verdict, "report_id": report.id}
    finally:
        db.close()


@celery_app.task(name="autosoc.health")
def health() -> dict:
    return {"status": "ok"}
