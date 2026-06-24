"""Symmetric encryption for secrets stored at rest (e.g. per-org provider keys).

Uses Fernet (AES-128-CBC + HMAC). The key is derived from ``SECRET_ENCRYPTION_KEY``
if set, otherwise from ``JWT_SECRET`` so the platform works out of the box while
still keeping ciphertext-at-rest. Provider secrets supplied via environment
variables are NOT stored in the DB and never reach this layer.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    raw = (getattr(settings, "secret_encryption_key", "") or settings.jwt_secret).encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        return ""


def mask_secret(secret: str | None) -> str:
    """Mask a secret for display: keep the last 4 chars, redact the rest."""
    if not secret:
        return ""
    s = str(secret)
    if len(s) <= 4:
        return "****"
    return "****" + s[-4:]
