"""PII / secret redaction used by the Privacy Guard before external AI calls."""
from __future__ import annotations

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_API_KEY = re.compile(r"\b(sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b")
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{10,}")


def redact_pii(text: str) -> str:
    """Redact emails, SSNs, card numbers and obvious secrets.

    IP addresses and hostnames are intentionally preserved because they are
    essential SOC indicators; customers needing stricter handling should use
    local-only mode where data never leaves the environment.
    """
    if not text:
        return text
    out = _API_KEY.sub("[REDACTED_SECRET]", text)
    out = _BEARER.sub("Bearer [REDACTED_TOKEN]", out)
    out = _EMAIL.sub("[REDACTED_EMAIL]", out)
    out = _SSN.sub("[REDACTED_SSN]", out)
    out = _CC.sub("[REDACTED_CARD]", out)
    return out


def contains_pii(text: str) -> bool:
    return bool(
        _EMAIL.search(text) or _SSN.search(text) or _API_KEY.search(text) or _CC.search(text)
    )
