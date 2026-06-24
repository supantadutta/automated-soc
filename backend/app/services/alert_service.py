"""Alert service: ingest alerts from text/JSON payloads."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import STATUS_NEW, Alert


def create_alert(
    db: Session,
    *,
    organization_id: int,
    customer_id: int | None,
    title: str,
    raw_payload: str,
    source_tool: str | None = None,
    severity: str = "Medium",
    ingest_method: str = "manual",
    raw_format: str = "text",
    actor_id: int | None = None,
) -> Alert:
    # Guard against oversized payloads (storage + AI token-cost / DoS vector).
    if raw_payload and len(raw_payload) > settings.max_alert_payload_chars:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"raw_payload exceeds {settings.max_alert_payload_chars} characters",
        )

    raw_json: dict[str, Any] | None = None
    detected_format = raw_format
    text = raw_payload

    # If the payload is JSON, capture it and derive a readable title.
    stripped = (raw_payload or "").strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                raw_json = parsed
                detected_format = "json"
                title = title or parsed.get("alert_name") or parsed.get("title") or "Imported Alert"
                source_tool = source_tool or parsed.get("source_tool") or parsed.get("tool")
                severity = parsed.get("severity") or severity
        except json.JSONDecodeError:
            pass

    alert = Alert(
        organization_id=organization_id, customer_id=customer_id, title=title or "Untitled Alert",
        source_tool=source_tool, severity=str(severity), status=STATUS_NEW,
        ingest_method=ingest_method, raw_format=detected_format, raw_payload=text,
        raw_json=raw_json, created_by=actor_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
