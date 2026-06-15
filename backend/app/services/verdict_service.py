"""Verdict engine: deterministic adjustment of AI verdicts based on hard signals.

This enforces the platform's safety rules independently of the LLM:
  - Weak evidence  -> Needs Review
  - Allowlisted source / known FP -> Benign Authorized Activity is permissible
  - Confirmed malicious IOC -> raise risk / support True Positive
"""
from __future__ import annotations

from typing import Any

VALID_VERDICTS = {
    "True Positive",
    "False Positive",
    "Benign Authorized Activity",
    "Duplicate",
    "Needs Review",
    "Escalated",
}


def evidence_strength(context: dict[str, Any]) -> int:
    strong = 0
    for key in ["src_ip", "username", "file_hash", "domain", "url"]:
        if context.get(key):
            strong += 1
    if context.get("malicious_iocs"):
        strong += 2
    if context.get("correlation_count", 0) >= 1:
        strong += 1
    return strong


def apply_rules(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    verdict = result.get("verdict")
    if verdict not in VALID_VERDICTS:
        verdict = "Needs Review"
        result["verdict"] = verdict

    confidence = int(result.get("confidence_score") or 0)
    strength = evidence_strength(context)
    malicious = context.get("malicious_iocs") or []
    allowlisted = bool(context.get("allowlisted"))
    prior_fp = bool(context.get("prior_false_positive"))
    duplicates = context.get("correlation_count", 0) >= 1 and not malicious

    notes: list[str] = []

    # Rule 1: malicious IOC strongly supports True Positive.
    if malicious and verdict not in {"True Positive", "Escalated"}:
        verdict = "True Positive"
        confidence = max(confidence, 70)
        notes.append("Elevated to True Positive due to confirmed malicious IOC(s).")

    # Rule 2: allowlist / known FP supports benign — but only without malicious IOCs.
    if (allowlisted or prior_fp) and not malicious and verdict == "Needs Review":
        verdict = "Benign Authorized Activity"
        confidence = max(confidence, 65)
        notes.append("Marked Benign Authorized Activity due to allowlist/known-FP match.")

    # Rule 3: weak evidence forces Needs Review (cannot assert TP/FP).
    if verdict in {"True Positive", "False Positive"} and strength < 2 and not malicious:
        verdict = "Needs Review"
        confidence = min(confidence, 45)
        notes.append("Downgraded to Needs Review: insufficient evidence to assert verdict.")

    # Clamp confidence.
    confidence = max(0, min(100, confidence))

    result["verdict"] = verdict
    result["confidence_score"] = confidence
    if notes:
        existing = result.get("reasoning_summary", "")
        result["reasoning_summary"] = (existing + " " + " ".join(notes)).strip()
        result.setdefault("qa_warnings", [])
        result["qa_warnings"] = list(dict.fromkeys(result["qa_warnings"] + notes))
    return result
