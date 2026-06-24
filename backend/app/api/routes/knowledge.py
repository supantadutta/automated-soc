"""Knowledge document (SOP / playbook / report-example) routes.

Documents are indexed into vector memory on creation so the Context Retrieval
agent can surface them during investigations (RAG).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.memory import memory
from app.api.deps import get_context, require_write
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.misc import KnowledgeDocument
from app.schemas import KnowledgeDocCreate, KnowledgeDocOut
from app.services import audit_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeDocOut])
def list_docs(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context),
              customer_id: int | None = None):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.organization_id == ctx.organization_id)
    if customer_id is not None:
        stmt = stmt.where(KnowledgeDocument.customer_id == customer_id)
    return db.execute(stmt.order_by(KnowledgeDocument.created_at.desc())).scalars().all()


@router.post("", response_model=KnowledgeDocOut, status_code=201)
def create_doc(payload: KnowledgeDocCreate, db: Session = Depends(get_db),
               ctx: TenantContext = Depends(require_write)):
    doc = KnowledgeDocument(
        organization_id=ctx.organization_id, customer_id=payload.customer_id,
        doc_type=payload.doc_type, title=payload.title, content=payload.content,
        created_by=ctx.user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # Index into vector memory for retrieval during investigations.
    memory.add(
        db, organization_id=ctx.organization_id, customer_id=payload.customer_id,
        source_type="sop" if payload.doc_type == "sop" else payload.doc_type,
        source_id=f"doc-{doc.id}", text=f"{payload.title}\n{payload.content}",
        meta={"title": payload.title, "doc_id": doc.id},
    )
    audit_service.record(db, organization_id=ctx.organization_id, action="knowledge.create",
                         actor_id=ctx.user_id, actor_email=ctx.email, target_type="knowledge",
                         target_id=doc.id)
    return doc
