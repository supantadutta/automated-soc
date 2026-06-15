"""Parser service: normalize a raw alert into structured fields, entities and IOCs."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import (
    STATUS_PARSED,
    Alert,
    Entity,
    IOC,
    NormalizedAlert,
)
from app.parsers import collect_iocs, detect_category, extract_entities, select_parser


def parse_alert(db: Session, alert: Alert) -> NormalizedAlert:
    raw_text = alert.raw_payload or ""
    raw_json = alert.raw_json if isinstance(alert.raw_json, dict) else None

    parser = select_parser(alert.source_tool)
    fields = parser(raw_text, raw_json)

    # Merge any text-extracted entities not already set.
    ents = extract_entities(raw_text)
    for key in ["src_ip", "dest_ip", "file_hash", "url", "domain"]:
        fields.setdefault(key, ents.get(key))
        if not fields.get(key):
            fields[key] = ents.get(key)

    fields["all_ips"] = ents.get("all_ips", [])
    fields["all_hashes"] = ents.get("all_hashes", [])
    fields["all_domains"] = ents.get("all_domains", [])
    fields["all_urls"] = ents.get("all_urls", [])

    alert_name = fields.get("alert_name") or alert.title
    category = detect_category(raw_text, alert_name)

    # Persist normalized alert (upsert).
    existing = db.execute(
        select(NormalizedAlert).where(NormalizedAlert.alert_id == alert.id)
    ).scalar_one_or_none()
    if existing is None:
        existing = NormalizedAlert(alert_id=alert.id, organization_id=alert.organization_id)
        db.add(existing)

    existing.alert_name = alert_name
    existing.source_tool = fields.get("source_tool") or alert.source_tool
    existing.severity = fields.get("severity") or alert.severity
    existing.event_time = str(fields.get("event_time")) if fields.get("event_time") else None
    existing.src_ip = fields.get("src_ip")
    existing.dest_ip = fields.get("dest_ip")
    existing.username = fields.get("username")
    existing.hostname = fields.get("hostname")
    existing.domain = fields.get("domain")
    existing.url = fields.get("url")
    existing.file_hash = fields.get("file_hash")
    existing.process_name = fields.get("process_name")
    existing.command_line = fields.get("command_line")
    existing.fields = {k: v for k, v in fields.items() if not k.startswith("all_")}

    alert.category = category
    alert.status = STATUS_PARSED

    # Rebuild entities and IOCs.
    db.query(Entity).filter(Entity.alert_id == alert.id).delete()
    db.query(IOC).filter(IOC.alert_id == alert.id).delete()

    for etype, key in [("ip", "src_ip"), ("ip", "dest_ip"), ("username", "username"),
                       ("hostname", "hostname"), ("domain", "domain"), ("hash", "file_hash"),
                       ("url", "url"), ("process", "process_name")]:
        val = fields.get(key)
        if val:
            db.add(Entity(alert_id=alert.id, organization_id=alert.organization_id,
                          entity_type=etype, value=str(val)))

    iocs = collect_iocs(fields)
    for ioc in iocs:
        db.add(IOC(alert_id=alert.id, organization_id=alert.organization_id,
                   ioc_type=ioc["ioc_type"], value=ioc["value"]))

    db.commit()
    db.refresh(existing)
    return existing


def normalized_to_dict(n: NormalizedAlert) -> dict[str, Any]:
    return {
        "alert_name": n.alert_name,
        "source_tool": n.source_tool,
        "severity": n.severity,
        "event_time": n.event_time,
        "src_ip": n.src_ip,
        "dest_ip": n.dest_ip,
        "username": n.username,
        "hostname": n.hostname,
        "domain": n.domain,
        "url": n.url,
        "file_hash": n.file_hash,
        "process_name": n.process_name,
        "command_line": n.command_line,
    }
