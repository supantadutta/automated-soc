"""Enrichment provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnrichmentResultData:
    provider: str
    ioc_type: str
    value: str
    verdict: str = "unknown"  # clean | suspicious | malicious | unknown
    risk_score: int = 0
    summary: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class EnrichmentProvider(ABC):
    name: str = "base"
    supported_types: set[str] = {"ip", "domain", "url", "hash"}

    def supports(self, ioc_type: str) -> bool:
        return ioc_type in self.supported_types

    @abstractmethod
    async def enrich(self, ioc_type: str, value: str) -> EnrichmentResultData:  # pragma: no cover
        ...
