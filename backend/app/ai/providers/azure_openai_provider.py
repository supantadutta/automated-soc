"""Azure OpenAI provider.

Azure uses deployment-scoped URLs and an ``api-key`` header instead of a Bearer
token, but the request/response body is OpenAI-compatible.
"""
from __future__ import annotations

import time

import httpx

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.ai.schemas import ProviderHealth
from app.core.config import settings


class AzureOpenAIProvider(OpenAICompatibleProvider):
    name = "azure_openai"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_openai_endpoint,
            model=model or settings.azure_openai_deployment,
        )
        self.deployment = settings.azure_openai_deployment
        self.api_version = settings.azure_openai_api_version

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.deployment)

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "api-key": self.api_key}

    def _url(self) -> str:
        return (
            f"{self.base_url}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )

    async def health_check(self) -> ProviderHealth:
        if not self.configured:
            return ProviderHealth(
                provider=self.name, configured=False, healthy=False,
                is_local=False, model=self.deployment,
                detail="Missing Azure endpoint, key or deployment.",
            )
        # A lightweight reachability check against the endpoint root.
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(self.base_url)
                healthy = resp.status_code < 500
                detail = f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            healthy, detail = False, f"unreachable: {type(exc).__name__}"
        return ProviderHealth(
            provider=self.name, configured=True, healthy=healthy, is_local=False,
            model=self.deployment, detail=detail,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
