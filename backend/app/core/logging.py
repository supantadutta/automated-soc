"""Structured logging with secret redaction.

We redact anything that looks like an API key, bearer token, or password from
log output so credentials never leak into logs (security requirement #14/#15).
"""
from __future__ import annotations

import logging
import re
import sys

_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key\"?\s*[:=]\s*\"?)([A-Za-z0-9_\-]{6,})", re.IGNORECASE),
    re.compile(r"(authorization\"?\s*[:=]\s*\"?bearer\s+)([A-Za-z0-9_\-\.]{6,})", re.IGNORECASE),
    re.compile(r"(password\"?\s*[:=]\s*\"?)([^\s\"]{3,})", re.IGNORECASE),
    re.compile(r"(sk-[A-Za-z0-9]{6,})"),
]


def redact_secrets(text: str) -> str:
    if not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        if pat.groups >= 2:
            out = pat.sub(lambda m: m.group(1) + "***REDACTED***", out)
        else:
            out = pat.sub("***REDACTED***", out)
    return out


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_secrets(original)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RedactingFormatter(
            fmt="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
