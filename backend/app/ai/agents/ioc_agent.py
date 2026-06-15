"""IOC Enrichment Agent — merges enrichment provider results into a normalized
IOC summary and risk assessment (deterministic merge, no AI required)."""
from __future__ import annotations

from typing import Any


class IOCEnrichmentAgent:
    name = "ioc_agent"

    def summarize(self, enrichment_by_ioc: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        summary: list[dict[str, Any]] = []
        for value, results in enrichment_by_ioc.items():
            if not results:
                continue
            risk = max((r.get("risk_score", 0) for r in results), default=0)
            verdicts = [r.get("verdict") for r in results if r.get("verdict")]
            reputation = "malicious" if any(v == "malicious" for v in verdicts) else (
                "suspicious" if any(v == "suspicious" for v in verdicts) else "clean"
            )
            summary.append(
                {
                    "ioc_type": results[0].get("ioc_type", "unknown"),
                    "value": value,
                    "reputation": reputation,
                    "risk_score": risk,
                    "sources": sorted({r.get("provider", "unknown") for r in results}),
                }
            )
        return summary

    def malicious_values(self, summary: list[dict[str, Any]]) -> list[str]:
        return [s["value"] for s in summary if s.get("reputation") == "malicious"]
