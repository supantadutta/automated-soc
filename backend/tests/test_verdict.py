"""Verdict engine rule tests."""
from __future__ import annotations

from app.services.verdict_service import apply_rules


def test_weak_evidence_forces_needs_review():
    result = {"verdict": "True Positive", "confidence_score": 90, "evidence": []}
    context = {"src_ip": None, "username": None, "malicious_iocs": [], "correlation_count": 0}
    out = apply_rules(result, context)
    assert out["verdict"] == "Needs Review"
    assert out["confidence_score"] <= 45


def test_malicious_ioc_elevates_to_true_positive():
    result = {"verdict": "Needs Review", "confidence_score": 40, "evidence": []}
    context = {"src_ip": "203.0.113.66", "username": "x", "malicious_iocs": ["beacon.evil-c2.example"],
               "correlation_count": 1}
    out = apply_rules(result, context)
    assert out["verdict"] == "True Positive"
    assert out["confidence_score"] >= 70


def test_allowlisted_supports_benign():
    result = {"verdict": "Needs Review", "confidence_score": 30, "evidence": []}
    context = {"src_ip": "192.168.143.84", "username": "svc-backup", "malicious_iocs": [],
               "allowlisted": True, "correlation_count": 0}
    out = apply_rules(result, context)
    assert out["verdict"] == "Benign Authorized Activity"


def test_invalid_verdict_defaults_to_needs_review():
    out = apply_rules({"verdict": "Definitely Hacked", "confidence_score": 99}, {})
    assert out["verdict"] == "Needs Review"
