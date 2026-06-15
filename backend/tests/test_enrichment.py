"""Mock enrichment determinism + known-bad detection."""
from __future__ import annotations

import asyncio

from app.enrichment import MockEnrichmentProvider


def test_mock_enrichment_is_stable():
    provider = MockEnrichmentProvider()
    a = asyncio.run(provider.enrich("ip", "8.8.8.8"))
    b = asyncio.run(provider.enrich("ip", "8.8.8.8"))
    assert a.verdict == b.verdict
    assert a.risk_score == b.risk_score


def test_known_bad_marker_is_malicious():
    provider = MockEnrichmentProvider()
    result = asyncio.run(provider.enrich("domain", "beacon.evil-c2.example"))
    assert result.verdict == "malicious"
    assert result.risk_score >= 80
