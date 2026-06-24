"""Vector memory retrieval and the analyst-feedback confidence loop."""
from __future__ import annotations

from app.ai.memory import VectorMemory, cosine, embed
from app.services.verdict_service import apply_rules


def test_embed_cosine_similar_texts_rank_higher():
    a = embed("brute force authentication failure from source ip")
    b = embed("repeated authentication failures brute force attack")
    c = embed("sql injection attempt blocked by web application firewall")
    assert cosine(a, b) > cosine(a, c)


def test_vector_memory_add_and_search(db):
    mem = VectorMemory(backend="memory")
    mem.add(db, organization_id=1, source_type="sop", source_id="s1",
            text="Globex sanctioned scanner runs from 192.168.143.84 during business hours")
    mem.add(db, organization_id=1, source_type="sop", source_id="s2",
            text="Initech C2 beaconing to known bad domains is a true positive")
    hits = mem.search(db, organization_id=1, query="scanner authentication 192.168.143.84", k=2)
    assert hits
    assert "scanner" in hits[0].text.lower()


def test_vector_memory_is_org_scoped(db):
    mem = VectorMemory()
    mem.add(db, organization_id=99, source_type="sop", source_id="x", text="secret org 99 content")
    hits = mem.search(db, organization_id=1, query="secret org 99 content")
    assert all("org 99" not in h.text for h in hits)


def test_feedback_signal_benign_reduces_tp_confidence():
    out = apply_rules(
        {"verdict": "True Positive", "confidence_score": 80, "evidence": [{"x": 1}]},
        {"src_ip": "203.0.113.10", "username": "jdoe", "malicious_iocs": [],
         "feedback_signal": "benign_leaning"},
    )
    assert out["confidence_score"] <= 70


def test_feedback_signal_malicious_raises_tp_confidence():
    out = apply_rules(
        {"verdict": "True Positive", "confidence_score": 60, "evidence": [{"x": 1}]},
        {"src_ip": "203.0.113.10", "username": "jdoe", "malicious_iocs": ["beacon.evil-c2.example"],
         "feedback_signal": "malicious_leaning"},
    )
    assert out["confidence_score"] >= 70
