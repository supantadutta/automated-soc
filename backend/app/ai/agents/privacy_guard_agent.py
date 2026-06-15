"""Privacy Guard Agent — decides whether data may leave the environment and
redacts PII/secrets before any external AI call (enforced again in AIRouter)."""
from __future__ import annotations

from app.ai.router import CustomerPolicy
from app.utils.redaction import contains_pii, redact_pii


class PrivacyGuardAgent:
    name = "privacy_guard_agent"

    def must_stay_local(self, policy: CustomerPolicy) -> bool:
        return policy.local_only_mode or not policy.external_ai_allowed

    def sanitize(self, text: str, policy: CustomerPolicy) -> tuple[str, bool]:
        if policy.redact_pii_before_ai and contains_pii(text):
            return redact_pii(text), True
        return text, False
