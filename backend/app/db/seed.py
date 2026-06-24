"""Database seeding: admin user, demo org, customers, allowlists, playbooks and
20 sample alerts. Idempotent — safe to run multiple times."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.base import Base
from app.db.seed_alerts import SAMPLE_ALERTS
from app.db.session import SessionLocal, engine
from app.models.customer import (
    Customer,
    CustomerAIPolicy,
    CustomerAllowlist,
    KnownFalsePositive,
)
from app.models.misc import Playbook
from app.models.user import ROLE_PLATFORM_ADMIN, Organization, User
from app.playbooks import PLAYBOOKS
from app.services.alert_service import create_alert

logger = get_logger("seed")


def seed(db: Session) -> None:
    # --- Organization + admin user ---
    org = db.execute(select(Organization).where(Organization.slug == "demo-soc")).scalar_one_or_none()
    if not org:
        org = Organization(name="AutoSOC Demo MSSP", slug="demo-soc", is_mssp=True,
                           description="Seeded demo organization")
        db.add(org)
        db.flush()

    admin = db.execute(select(User).where(User.email == settings.seed_admin_email)).scalar_one_or_none()
    if not admin:
        admin = User(
            organization_id=org.id, email=settings.seed_admin_email, full_name="SOC Administrator",
            hashed_password=hash_password(settings.seed_admin_password),
            role=ROLE_PLATFORM_ADMIN, is_active=True,
        )
        db.add(admin)
        db.flush()
        logger.info("Seeded admin user %s", settings.seed_admin_email)

    # --- Customers ---
    customers: dict[str, Customer] = {}
    for name, industry, crit in [("Globex", "Manufacturing", "high"), ("Initech", "Finance", "critical")]:
        cust = db.execute(
            select(Customer).where(Customer.organization_id == org.id, Customer.name == name)
        ).scalar_one_or_none()
        if not cust:
            cust = Customer(organization_id=org.id, name=name, industry=industry,
                           criticality=crit, contact_email=f"soc@{name.lower()}.test",
                           created_by=admin.id)
            db.add(cust)
            db.flush()
            db.add(CustomerAIPolicy(customer_id=cust.id, organization_id=org.id))
        customers[name] = cust

    # --- Allowlists & known false positives ---
    if not db.execute(select(CustomerAllowlist).where(CustomerAllowlist.organization_id == org.id)).first():
        db.add_all([
            CustomerAllowlist(organization_id=org.id, customer_id=customers["Globex"].id,
                              entry_type="ip", value="192.168.143.84",
                              reason="Sanctioned internal vulnerability scanner", created_by=admin.id),
            CustomerAllowlist(organization_id=org.id, customer_id=customers["Initech"].id,
                              entry_type="username", value="svc-backup",
                              reason="Approved backup service account", created_by=admin.id),
        ])
        db.add(KnownFalsePositive(organization_id=org.id, customer_id=customers["Globex"].id,
                                  alert_name="New Endpoint Usage",
                                  reason="Frequent laptop refreshes create first-seen noise",
                                  created_by=admin.id))

    # --- Playbooks ---
    for pb in PLAYBOOKS:
        existing = db.execute(select(Playbook).where(Playbook.key == pb["key"])).scalar_one_or_none()
        if not existing:
            db.add(Playbook(organization_id=org.id, **pb))

    db.commit()

    # --- Default versioned prompt templates ---
    from app.services.prompt_service import seed_default_prompts

    seed_default_prompts(db, org.id)

    # --- Customer SOPs (indexed into vector memory for RAG retrieval) ---
    from app.ai.memory import memory
    from app.models.misc import KnowledgeDocument

    sops = [
        (customers["Globex"].id, "Globex Authentication SOP",
         "Globex runs a sanctioned vulnerability scanner from 192.168.143.84. "
         "Authentication spikes from this host during business hours are expected. "
         "Confirm the scan window before escalating brute-force or AD auth alerts."),
        (customers["Globex"].id, "Globex Web Application SOP",
         "Globex public portals sit behind an F5 WAF. WAF-blocked SQLi/XSS attempts "
         "are routine internet noise; escalate only on signs of successful exploitation "
         "or WAF bypass."),
        (customers["Initech"].id, "Initech Privileged Access SOP",
         "Initech admin-ops performs scheduled maintenance via PsExec to HR and FIN "
         "servers on Tuesdays 02:00-04:00. Lateral-movement alerts in that window may be "
         "authorized; verify the change ticket before containment."),
        (customers["Initech"].id, "Initech C2 Response SOP",
         "Any confirmed beaconing to a known-bad C2 domain is treated as a true positive. "
         "Validate the host in EDR and raise an approval request for isolation."),
    ]
    if not db.execute(select(KnowledgeDocument).where(KnowledgeDocument.organization_id == org.id)).first():
        for cust_id, title, content in sops:
            doc = KnowledgeDocument(organization_id=org.id, customer_id=cust_id, doc_type="sop",
                                    title=title, content=content, created_by=admin.id)
            db.add(doc)
            db.flush()
            memory.add(db, organization_id=org.id, customer_id=cust_id, source_type="sop",
                       source_id=f"doc-{doc.id}", text=f"{title}\n{content}", meta={"title": title})
        logger.info("Seeded %d customer SOPs into vector memory", len(sops))

    # --- Sample alerts ---
    from app.models.alert import Alert

    existing_count = db.execute(
        select(Alert).where(Alert.organization_id == org.id)
    ).scalars().all()
    if len(existing_count) < len(SAMPLE_ALERTS):
        existing_titles = {a.title for a in existing_count}
        for item in SAMPLE_ALERTS:
            if item["title"] in existing_titles:
                continue
            cust = customers.get(item.get("customer", "Globex"))
            create_alert(
                db, organization_id=org.id, customer_id=cust.id if cust else None,
                title=item["title"], raw_payload=item["raw"], source_tool=item["source_tool"],
                severity=item["severity"], ingest_method="seed", actor_id=admin.id,
            )
        logger.info("Seeded %d sample alerts", len(SAMPLE_ALERTS))

    logger.info("Seeding complete.")


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
