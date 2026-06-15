"""Cost Optimizer Agent — recommends a provider tier based on alert severity and
routing mode (local/cheap for low severity, premium for critical)."""
from __future__ import annotations

from app.ai.router import CustomerPolicy


class CostOptimizerAgent:
    name = "cost_optimizer_agent"

    def recommend_mode(self, severity: str, base_mode: str, policy: CustomerPolicy) -> str:
        if policy.local_only_mode or not policy.external_ai_allowed:
            return "privacy"
        if base_mode and base_mode != "auto":
            return base_mode
        sev = (severity or "").lower()
        if sev in {"critical", "high"}:
            return "soc_critical"
        if sev in {"informational", "low"}:
            return "cost"
        return "auto"
