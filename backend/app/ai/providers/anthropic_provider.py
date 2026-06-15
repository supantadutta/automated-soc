"""Anthropic Claude provider (Messages API)."""
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


class AnthropicProvider(AIProvider):
    name = "anthropic"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(model or settings.anthropic_model)
        self.api_key = settings.anthropic_api_key
        self.base_url = settings.anthropic_base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _post(self, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/messages", headers=self._headers(), json=payload
            )
            if resp.status_code >= 400:
                raise AIProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()

    async def generate(self, request: AIRequest) -> AIResponse:
        if not self.configured:
            raise AIProviderError(self.name, "provider not configured")
        started = time.perf_counter()
        model = request.model or self.model

        system = "\n".join(m.content for m in request.messages if m.role == "system")
        msgs = [
            {"role": m.role, "content": m.content}
            for m in request.messages
            if m.role in {"user", "assistant"}
        ]
        if request.json_mode:
            system += "\n\nRespond with a single valid JSON object and nothing else."

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": msgs or [{"role": "user", "content": " "}],
        }
        if system.strip():
            payload["system"] = system
        try:
            data = await self._post(payload, request.timeout)
        except httpx.HTTPError as exc:
            raise AIProviderError(self.name, f"request failed: {type(exc).__name__}") from exc

        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("input_tokens")
            or sum(estimate_tokens(m.content) for m in request.messages),
            output_tokens=usage_data.get("output_tokens") or estimate_tokens(text),
        )
        return self._finalize(text, model or "anthropic", usage, started, raw=usage_data)

    async def health_check(self) -> ProviderHealth:
        if not self.configured:
            return ProviderHealth(
                provider=self.name, configured=False, healthy=False, is_local=False,
                model=self.model, detail="Missing ANTHROPIC_API_KEY.",
            )
        # Minimal ping using a 1-token completion.
        started = time.perf_counter()
        try:
            await self._post(
                {
                    "model": self.model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                8,
            )
            healthy, detail = True, "ok"
        except Exception as exc:  # noqa: BLE001 - normalize
            healthy, detail = False, str(exc)[:120]
        return ProviderHealth(
            provider=self.name, configured=True, healthy=healthy, is_local=False,
            model=self.model, detail=detail,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
