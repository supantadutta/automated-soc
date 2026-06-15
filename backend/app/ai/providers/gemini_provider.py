"""Google Gemini provider (generateContent REST API)."""
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


class GeminiProvider(AIProvider):
    name = "gemini"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(model or settings.gemini_model)
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _post(self, url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 400:
                raise AIProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()

    async def generate(self, request: AIRequest) -> AIResponse:
        if not self.configured:
            raise AIProviderError(self.name, "provider not configured")
        started = time.perf_counter()
        model = request.model or self.model
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"

        system = "\n".join(m.content for m in request.messages if m.role == "system")
        contents = []
        for m in request.messages:
            if m.role == "system":
                continue
            contents.append(
                {"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]}
            )
        gen_config: dict[str, Any] = {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        }
        if request.json_mode:
            gen_config["responseMimeType"] = "application/json"
        payload: dict[str, Any] = {"contents": contents, "generationConfig": gen_config}
        if system.strip():
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        try:
            data = await self._post(url, payload, request.timeout)
        except httpx.HTTPError as exc:
            raise AIProviderError(self.name, f"request failed: {type(exc).__name__}") from exc

        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
        usage_data = data.get("usageMetadata", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("promptTokenCount")
            or sum(estimate_tokens(m.content) for m in request.messages),
            output_tokens=usage_data.get("candidatesTokenCount") or estimate_tokens(text),
        )
        return self._finalize(text, model or "gemini", usage, started, raw=usage_data)

    async def health_check(self) -> ProviderHealth:
        if not self.configured:
            return ProviderHealth(
                provider=self.name, configured=False, healthy=False, is_local=False,
                model=self.model, detail="Missing GEMINI_API_KEY.",
            )
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(f"{self.base_url}/models?key={self.api_key}")
                healthy = resp.status_code == 200
                detail = f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            healthy, detail = False, f"unreachable: {type(exc).__name__}"
        return ProviderHealth(
            provider=self.name, configured=True, healthy=healthy, is_local=False,
            model=self.model, detail=detail,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
