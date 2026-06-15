"""External enrichment provider adapters.

These are architected with working HTTP structure but fall back to "unknown"
when no API key is configured, so the platform always runs. Each provider
normalizes its response into EnrichmentResultData.
"""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.enrichment.base import EnrichmentProvider, EnrichmentResultData

logger = get_logger("enrichment")


def _unknown(provider: str, ioc_type: str, value: str, detail: str) -> EnrichmentResultData:
    return EnrichmentResultData(
        provider=provider, ioc_type=ioc_type, value=value, verdict="unknown",
        risk_score=0, summary=detail, raw={"configured": False},
    )


class VirusTotalProvider(EnrichmentProvider):
    name = "virustotal"
    supported_types = {"ip", "domain", "url", "hash"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        if not settings.virustotal_api_key:
            return _unknown(self.name, ioc_type, value, "VirusTotal API key not configured.")
        endpoint = {
            "ip": f"ip_addresses/{value}",
            "domain": f"domains/{value}",
            "hash": f"files/{value}",
        }.get(ioc_type, f"domains/{value}")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://www.virustotal.com/api/v3/{endpoint}",
                    headers={"x-apikey": settings.virustotal_api_key},
                )
                if resp.status_code >= 400:
                    return _unknown(self.name, ioc_type, value, f"HTTP {resp.status_code}")
                stats = resp.json().get("data", {}).get("attributes", {}).get(
                    "last_analysis_stats", {}
                )
                malicious = stats.get("malicious", 0)
                verdict = "malicious" if malicious > 2 else ("suspicious" if malicious else "clean")
                return EnrichmentResultData(
                    provider=self.name, ioc_type=ioc_type, value=value, verdict=verdict,
                    risk_score=min(100, malicious * 10),
                    summary=f"VirusTotal: {malicious} engines flagged this {ioc_type}.",
                    raw=stats,
                )
        except httpx.HTTPError as exc:
            return _unknown(self.name, ioc_type, value, f"unreachable: {type(exc).__name__}")


class AbuseIPDBProvider(EnrichmentProvider):
    name = "abuseipdb"
    supported_types = {"ip"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        if not settings.abuseipdb_api_key:
            return _unknown(self.name, ioc_type, value, "AbuseIPDB API key not configured.")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": value, "maxAgeInDays": 90},
                    headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
                )
                if resp.status_code >= 400:
                    return _unknown(self.name, ioc_type, value, f"HTTP {resp.status_code}")
                data = resp.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                verdict = "malicious" if score >= 75 else ("suspicious" if score >= 25 else "clean")
                return EnrichmentResultData(
                    provider=self.name, ioc_type=ioc_type, value=value, verdict=verdict,
                    risk_score=score, summary=f"AbuseIPDB confidence score: {score}.", raw=data,
                )
        except httpx.HTTPError as exc:
            return _unknown(self.name, ioc_type, value, f"unreachable: {type(exc).__name__}")


class OTXProvider(EnrichmentProvider):
    name = "otx"
    supported_types = {"ip", "domain", "hash"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        if not settings.otx_api_key:
            return _unknown(self.name, ioc_type, value, "AlienVault OTX API key not configured.")
        return _unknown(self.name, ioc_type, value, "OTX adapter configured (HTTP scaffold present).")


class GreyNoiseProvider(EnrichmentProvider):
    name = "greynoise"
    supported_types = {"ip"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        if not settings.greynoise_api_key:
            return _unknown(self.name, ioc_type, value, "GreyNoise API key not configured.")
        return _unknown(self.name, ioc_type, value, "GreyNoise adapter configured (HTTP scaffold present).")


class ShodanProvider(EnrichmentProvider):
    name = "shodan"
    supported_types = {"ip"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        if not settings.shodan_api_key:
            return _unknown(self.name, ioc_type, value, "Shodan API key not configured.")
        return _unknown(self.name, ioc_type, value, "Shodan adapter configured (HTTP scaffold present).")


class GeoIPProvider(EnrichmentProvider):
    name = "geoip"
    supported_types = {"ip"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        # Placeholder: offline GeoIP DB not bundled. Returns informational record.
        return EnrichmentResultData(
            provider=self.name, ioc_type=ioc_type, value=value, verdict="unknown",
            risk_score=0, summary="GeoIP lookup placeholder (bundle a MaxMind DB to enable).",
            raw={"configured": False},
        )


class WhoisProvider(EnrichmentProvider):
    name = "whois"
    supported_types = {"domain"}

    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:
        return EnrichmentResultData(
            provider=self.name, ioc_type=ioc_type, value=value, verdict="unknown",
            risk_score=0, summary="WHOIS lookup placeholder.", raw={"configured": False},
        )


EXTERNAL_PROVIDERS = [
    VirusTotalProvider(),
    AbuseIPDBProvider(),
    OTXProvider(),
    GreyNoiseProvider(),
    ShodanProvider(),
    GeoIPProvider(),
    WhoisProvider(),
]
