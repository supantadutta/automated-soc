"""Shared implementation for any OpenAI Chat Completions compatible endpoint.

OpenAI, Azure (via deployment), Groq, OpenRouter, Mistral, DeepSeek, Together,
LM Studio, vLLM and generic self-hosted servers all speak this dialect, so they
subclass this with the right base URL / auth header.
"""
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


class OpenAICompatibleProvider(AIProvider):
    name = "openai_compatible"
    is_local = False

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str | None = None,
        extra_headers: dict[str, str] | None = None,
        auth_scheme: str = "Bearer",
    ):
        super().__init__(model)
        self.api_key = api_key or ""
        self.base_url = (base_url or "").rstrip("/")
        self.extra_headers = extra_headers or {}
        self.auth_scheme = auth_scheme

    # ------------------------------------------------------------------ config
    @property
    def configured(self) -> bool:
        # Local servers do not require an API key.
        if self.is_local:
            return bool(self.base_url)
        return bool(self.api_key and self.base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"{self.auth_scheme} {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    def _payload(self, request: AIRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model or self.model,
            "messages": request.to_openai_messages(),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _url(self) -> str:
        return f"{self.base_url}/chat/completions"

    # ------------------------------------------------------------------- calls
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    async def _post(self, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(self._url(), headers=self._headers(), json=payload)
            if resp.status_code >= 400:
                # Normalize error and never echo back auth headers/keys.
                snippet = resp.text[:300] if resp.text else ""
                raise AIProviderError(self.name, f"HTTP {resp.status_code}: {snippet}", resp.status_code)
            return resp.json()

    async def generate(self, request: AIRequest) -> AIResponse:
        if not self.configured:
            raise AIProviderError(self.name, "provider not configured")
        started = time.perf_counter()
        model = request.model or self.model or "unknown"
        try:
            data = await self._post(self._payload(request), request.timeout)
        except httpx.HTTPError as exc:
            raise AIProviderError(self.name, f"request failed: {type(exc).__name__}") from exc

        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content", "") or ""
        usage_data = data.get("usage") or {}
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens")
            or sum(estimate_tokens(m.content) for m in request.messages),
            output_tokens=usage_data.get("completion_tokens") or estimate_tokens(text),
        )
        return self._finalize(
            text, data.get("model", model), usage, started, raw=usage_data,
            finish_reason=choice.get("finish_reason"),
        )

    async def stream(self, request: AIRequest):
        """Stream tokens via SSE (OpenAI-compatible ``stream: true``)."""
        if not self.configured:
            raise AIProviderError(self.name, "provider not configured")
        import json as _json

        payload = self._payload(request)
        payload["stream"] = True
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            async with client.stream("POST", self._url(), headers=self._headers(), json=payload) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    raise AIProviderError(self.name, f"HTTP {resp.status_code}", resp.status_code)
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = _json.loads(data)
                    except ValueError:
                        continue
                    delta = (obj.get("choices") or [{}])[0].get("delta", {}).get("content")
                    if delta:
                        yield delta

    async def health_check(self) -> ProviderHealth:
        if not self.configured:
            return ProviderHealth(
                provider=self.name, configured=False, healthy=False,
                is_local=self.is_local, model=self.model,
                detail="Missing API key or base URL.",
            )
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
                healthy = resp.status_code < 500
                detail = f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            healthy, detail = False, f"unreachable: {type(exc).__name__}"
        return ProviderHealth(
            provider=self.name, configured=True, healthy=healthy,
            is_local=self.is_local, model=self.model, detail=detail,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
