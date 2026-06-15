"""Abstract AI provider interface and shared helpers.

Every concrete provider implements the unified contract:
    generate, generate_json, health_check, estimate_cost
"""
from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from app.ai.schemas import (
    AIRequest,
    AIResponse,
    CostEstimate,
    ProviderHealth,
    TokenUsage,
)

# Rough per-1K-token pricing (USD) used for cost estimation when providers do
# not report it. Local models are zero-cost.
PRICING_PER_1K = {
    "gpt-4.1": (0.0025, 0.01),
    "gpt-4.1-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-opus-4-8": (0.015, 0.075),
    "gemini-1.5-pro": (0.00125, 0.005),
    "mistral-large-latest": (0.002, 0.006),
    "command-r-plus": (0.0025, 0.01),
    "llama-3.1-70b-versatile": (0.00059, 0.00079),
    "_default": (0.0005, 0.0015),
}


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token) for cost tracking without tiktoken."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def price_for(model: str) -> tuple[float, float]:
    return PRICING_PER_1K.get(model, PRICING_PER_1K["_default"])


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response."""
    if not text:
        raise ValueError("empty response")
    candidate = text.strip()
    fence = _FENCE.search(candidate)
    if fence:
        candidate = fence.group(1).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        block = _JSON_BLOCK.search(candidate)
        if block:
            return json.loads(block.group(0))
        raise


class AIProvider(ABC):
    name: str = "base"
    is_local: bool = False

    def __init__(self, model: str | None = None):
        self.model = model

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:  # pragma: no cover
        ...

    async def generate_json(
        self, request: AIRequest, schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Default JSON generation: ask for JSON, then parse defensively."""
        request.json_mode = True
        response = await self.generate(request)
        return extract_json(response.text)

    @abstractmethod
    async def health_check(self) -> ProviderHealth:  # pragma: no cover
        ...

    async def estimate_cost(self, request: AIRequest) -> CostEstimate:
        model = request.model or self.model or "_default"
        in_tokens = sum(estimate_tokens(m.content) for m in request.messages)
        out_tokens = request.max_tokens // 2
        if self.is_local:
            cost = 0.0
        else:
            in_price, out_price = price_for(model)
            cost = (in_tokens / 1000) * in_price + (out_tokens / 1000) * out_price
        return CostEstimate(
            provider=self.name,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            estimated_cost=round(cost, 6),
        )

    def _finalize(
        self,
        text: str,
        model: str,
        usage: TokenUsage,
        started: float,
        raw: dict[str, Any] | None = None,
        finish_reason: str | None = None,
    ) -> AIResponse:
        latency = int((time.perf_counter() - started) * 1000)
        if self.is_local:
            cost = 0.0
        else:
            # Prefer the capability registry (per-token) as the single source of
            # truth; fall back to coarse per-1K pricing for unknown models.
            from app.ai.capabilities import MODEL_CAPABILITIES, estimate_cost_tokens

            if model in MODEL_CAPABILITIES:
                cost = estimate_cost_tokens(model, usage.input_tokens, usage.output_tokens, self.name)
            else:
                in_price, out_price = price_for(model)
                cost = (usage.input_tokens / 1000) * in_price + (
                    usage.output_tokens / 1000
                ) * out_price
        return AIResponse(
            text=text,
            provider=self.name,
            model=model,
            usage=usage,
            latency_ms=latency,
            estimated_cost=round(cost, 6),
            raw=raw or {},
            finish_reason=finish_reason,
        )
