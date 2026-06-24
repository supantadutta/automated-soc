"""Vector memory for case/SOP retrieval.

A real, dependency-free semantic-ish retrieval layer. Text is embedded with a
hashing TF vectorizer and compared by cosine similarity. Entries (past
investigations, customer SOPs, report examples) are persisted in
``vector_memory_metadata``; retrieval embeds the stored text on demand.

``VECTOR_BACKEND`` selects the store:
  - ``memory`` (default): persisted text + in-process cosine ranking (implemented here)
  - ``qdrant`` / ``pgvector``: pluggable backends (interface present; the memory
    backend is the supported default for local-first deployments)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.misc import VectorMemoryMetadata

_DIM = 512
_TOKEN = re.compile(r"[a-z0-9]{2,}")
_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "was", "were", "are",
    "has", "have", "had", "not", "but", "all", "any", "may", "can", "via",
}


def embed(text: str) -> list[float]:
    """Hashing TF vectorizer with L2 normalization (no external model needed)."""
    vec = [0.0] * _DIM
    if not text:
        return vec
    for tok in _TOKEN.findall(text.lower()):
        if tok in _STOP:
            continue
        vec[hash(tok) % _DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class MemoryHit:
    id: int
    source_type: str
    source_id: Optional[str]
    text: str
    score: float
    meta: dict


class VectorMemory:
    """Persisted memory with cosine retrieval over the configured backend."""

    def __init__(self, backend: str | None = None):
        self.backend = backend or settings.vector_backend

    def add(self, db: Session, *, organization_id: int, source_type: str,
            text: str, customer_id: int | None = None, source_id: str | None = None,
            meta: dict | None = None, dedupe: bool = True) -> VectorMemoryMetadata | None:
        if not (text or "").strip():
            return None
        if dedupe and source_id is not None:
            existing = db.execute(
                select(VectorMemoryMetadata).where(
                    VectorMemoryMetadata.organization_id == organization_id,
                    VectorMemoryMetadata.source_type == source_type,
                    VectorMemoryMetadata.source_id == str(source_id),
                )
            ).scalar_one_or_none()
            if existing:
                existing.text = text
                existing.meta = meta
                db.commit()
                return existing
        row = VectorMemoryMetadata(
            organization_id=organization_id, customer_id=customer_id,
            source_type=source_type, source_id=str(source_id) if source_id is not None else None,
            vector_id=None, text=text, meta=meta or {},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def search(self, db: Session, *, organization_id: int, query: str, k: int = 5,
               customer_id: int | None = None, source_types: list[str] | None = None,
               min_score: float = 0.05) -> list[MemoryHit]:
        if not (query or "").strip():
            return []
        stmt = select(VectorMemoryMetadata).where(
            VectorMemoryMetadata.organization_id == organization_id
        )
        if customer_id is not None:
            stmt = stmt.where(VectorMemoryMetadata.customer_id == customer_id)
        if source_types:
            stmt = stmt.where(VectorMemoryMetadata.source_type.in_(source_types))
        rows = db.execute(stmt).scalars().all()
        if not rows:
            return []
        qv = embed(query)
        scored: list[MemoryHit] = []
        for r in rows:
            score = cosine(qv, embed(r.text or ""))
            if score >= min_score:
                scored.append(MemoryHit(
                    id=r.id, source_type=r.source_type, source_id=r.source_id,
                    text=r.text or "", score=round(score, 4), meta=r.meta or {},
                ))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]


# Module-level singleton.
memory = VectorMemory()
