"""Cohere provider (Chat API v2)."""
from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import AIProvider, estimate_tokens
from app.ai.schemas import (
    AIProviderError,
    AIRequest,
    AIResponse,
    ProviderHealth,
    TokenUsage,
)
from app.core.config import settings


class CohereProvider(AIProvider):
    name = "cohere"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(model or settings.cohere_model)
        self.api_key = settings.cohere_api_key
        self.base_url = "https://api.cohere.com/v2"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _post(self, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat", headers=self._headers(), json=payload
            )
            if resp.status_code >= 400:
                raise AIProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()

    async def generate(self, request: AIRequest) -> AIResponse:
        if not self.configured:
            raise AIProviderError(self.name, "provider not configured")
        started = time.perf_counter()
        model = request.model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "messages": request.to_openai_messages(),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            data = await self._post(payload, request.timeout)
        except httpx.HTTPError as exc:
            raise AIProviderError(self.name, f"request failed: {type(exc).__name__}") from exc

        text = ""
        msg = data.get("message", {})
        for part in msg.get("content", []) or []:
            text += part.get("text", "")
        billed = data.get("usage", {}).get("billed_units", {})
        usage = TokenUsage(
            input_tokens=billed.get("input_tokens")
            or sum(estimate_tokens(m.content) for m in request.messages),
            output_tokens=billed.get("output_tokens") or estimate_tokens(text),
        )
        return self._finalize(text, model or "cohere", usage, started, raw=billed)

    async def health_check(self) -> ProviderHealth:
        configured = self.configured
        return ProviderHealth(
            provider=self.name, configured=configured, healthy=configured, is_local=False,
            model=self.model,
            detail="Configured (key present)." if configured else "Missing COHERE_API_KEY.",
        )
