"""Deterministic mock enrichment provider.

Returns stable, repeatable results derived from a hash of the IOC value so demos
and tests are reproducible without external API keys. Values containing known
"bad" markers (used by the seed data) are flagged malicious.
"""
from __future__ import annotations

import hashlib

from app.enrichment.base import EnrichmentProvider, EnrichmentResultData

# Markers used in the seeded sample alerts to demonstrate malicious verdicts.
KNOWN_BAD_MARKERS = ("evil", "malicious", "c2", "badactor", "203.0.113.66", "198.51.100.23")


class MockEnrichmentProvider(EnrichmentProvider):
    name = "mock"
    supported_types = {"ip", "domain", "url", "hash", "email", "hostname", "username"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        lowered = value.lower()
        if any(m in lowered for m in KNOWN_BAD_MARKERS):
            return EnrichmentResultData(
                provider=self.name, ioc_type=ioc_type, value=value,
                verdict="malicious", risk_score=88,
                summary=f"{ioc_type} '{value}' matches known-bad threat intel markers.",
                raw={"source": "mock", "matched_marker": True},
            )

        digest = int(hashlib.sha256(value.encode()).hexdigest(), 16)
        bucket = digest % 100
        if bucket >= 92:
            verdict, score = "malicious", 80 + bucket % 20
        elif bucket >= 75:
            verdict, score = "suspicious", 45 + bucket % 25
        else:
            verdict, score = "clean", bucket % 25
        return EnrichmentResultData(
            provider=self.name, ioc_type=ioc_type, value=value,
            verdict=verdict, risk_score=score,
            summary=f"Mock enrichment for {ioc_type} '{value}': {verdict} (score {score}).",
            raw={"source": "mock", "bucket": bucket},
        )
