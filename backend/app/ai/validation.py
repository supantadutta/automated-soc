"""Structured-output reliability helpers.

Pipeline used by agents that require JSON:
  1. parse (lenient extraction)
  2. repair common LLM JSON mistakes
  3. validate/coerce against the expected shape
  4. report completeness warnings (drives QA "Needs Review")
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.ai.schemas import empty_investigation

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
_OBJ = re.compile(r"\{.*\}", re.DOTALL)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
_SMART_QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def repair_json(text: str) -> str:
    """Best-effort repair of common LLM JSON defects, returns a JSON string."""
    if not text:
        return "{}"
    s = text.strip()
    fence = _FENCE.search(s)
    if fence:
        s = fence.group(1).strip()
    for bad, good in _SMART_QUOTES.items():
        s = s.replace(bad, good)
    # Trim to the outermost object if there's surrounding prose.
    if not s.startswith("{"):
        m = _OBJ.search(s)
        if m:
            s = m.group(0)
    s = _TRAILING_COMMA.sub(r"\1", s)
    return s


def parse_json_lenient(text: str) -> dict[str, Any] | None:
    """Try strict parse, then repaired parse. Returns None if both fail."""
    if not text:
        return None
    try:
        val = json.loads(text)
        return val if isinstance(val, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        val = json.loads(repair_json(text))
        return val if isinstance(val, dict) else None
    except json.JSONDecodeError:
        return None


# Fields required for a usable investigation result.
_REQUIRED_FIELDS = ["verdict", "confidence_score", "executive_summary"]
_LIST_FIELDS = [
    "facts_observed", "assumptions", "evidence", "missing_evidence", "ioc_summary",
    "mitre_mapping", "timeline", "recommended_actions", "investigation_checklist", "qa_warnings",
]
_VALID_VERDICTS = {
    "True Positive", "False Positive", "Benign Authorized Activity",
    "Duplicate", "Needs Review", "Escalated",
}


def coerce_investigation(data: dict[str, Any]) -> dict[str, Any]:
    """Merge model output onto the canonical schema and normalize types."""
    base = empty_investigation()
    if isinstance(data, dict):
        for k, v in data.items():
            if v is not None:
                base[k] = v
    # Normalize verdict.
    if base.get("verdict") not in _VALID_VERDICTS:
        base["verdict"] = "Needs Review"
    # Clamp confidence to 0-100 int.
    try:
        base["confidence_score"] = max(0, min(100, int(float(base.get("confidence_score") or 0))))
    except (TypeError, ValueError):
        base["confidence_score"] = 0
    # Ensure list fields are lists.
    for f in _LIST_FIELDS:
        if not isinstance(base.get(f), list):
            base[f] = []
    # Ensure detection query dict.
    if not isinstance(base.get("detection_query_suggestions"), dict):
        base["detection_query_suggestions"] = empty_investigation()["detection_query_suggestions"]
    return base


def completeness_warnings(result: dict[str, Any]) -> list[str]:
    """Flag incomplete output that should reduce confidence / force review."""
    warnings: list[str] = []
    if not (result.get("executive_summary") or "").strip():
        warnings.append("Executive summary is empty.")
    if not (result.get("technical_analysis") or "").strip():
        warnings.append("Technical analysis is empty.")
    if result.get("verdict") in {"True Positive", "False Positive"} and not result.get("evidence"):
        warnings.append("Verdict asserted without supporting evidence.")
    if not result.get("missing_evidence"):
        warnings.append("Missing-evidence section is empty (an investigation should state gaps).")
    if not result.get("recommended_actions"):
        warnings.append("No recommended next steps provided.")
    return warnings


def is_valid_investigation(data: dict[str, Any] | None) -> bool:
    if not isinstance(data, dict):
        return False
    return all(data.get(f) not in (None, "") for f in _REQUIRED_FIELDS)
