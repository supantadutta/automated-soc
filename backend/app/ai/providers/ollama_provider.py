"""Ollama local LLM provider (native /api/chat endpoint)."""
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


class OllamaProvider(AIProvider):
    name = "ollama"
    is_local = True

    def __init__(self, model: str | None = None):
        super().__init__(model or settings.ollama_model)
        self.base_url = settings.ollama_base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _post(self, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            if resp.status_code >= 400:
                raise AIProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()

    async def generate(self, request: AIRequest) -> AIResponse:
        started = time.perf_counter()
        model = request.model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "messages": request.to_openai_messages(),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.json_mode:
            payload["format"] = "json"
        try:
            data = await self._post(payload, request.timeout)
        except httpx.HTTPError as exc:
            raise AIProviderError(self.name, f"request failed: {type(exc).__name__}") from exc

        text = (data.get("message") or {}).get("content", "") or ""
        usage = TokenUsage(
            input_tokens=data.get("prompt_eval_count")
            or sum(estimate_tokens(m.content) for m in request.messages),
            output_tokens=data.get("eval_count") or estimate_tokens(text),
        )
        return self._finalize(text, model or "ollama", usage, started, raw={})

    async def health_check(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                healthy = resp.status_code == 200
                models = []
                if healthy:
                    models = [m.get("name") for m in resp.json().get("models", [])]
                detail = f"models: {', '.join(models[:5])}" if models else f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            healthy, detail = False, f"unreachable: {type(exc).__name__}"
        return ProviderHealth(
            provider=self.name, configured=True, healthy=healthy, is_local=True,
            model=self.model, detail=detail,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
