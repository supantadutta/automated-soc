"""Model Capability Registry.

A central catalog of what each model/provider can do and what it costs. Used by
the AI gateway for capability-aware model selection (e.g. require JSON support,
respect privacy level, prefer a latency class) and by the API/UI to surface
model metadata.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class ModelCapability:
    provider: str
    model: str
    supports_json: bool = True
    supports_tools: bool = False
    supports_streaming: bool = True
    supports_vision: bool = False
    max_context_tokens: int = 8192
    cost_per_input_token: float = 0.0       # USD per token
    cost_per_output_token: float = 0.0      # USD per token
    recommended_for: list[str] = field(default_factory=list)
    privacy_level: str = "external"         # local | external
    latency_class: str = "medium"           # fast | medium | slow

    def to_dict(self) -> dict:
        return asdict(self)


def _c(provider, model, **kw) -> ModelCapability:
    return ModelCapability(provider=provider, model=model, **kw)


# Per-1M-token pricing is converted to per-token below for convenience.
def _per_m(input_per_m: float, output_per_m: float) -> dict:
    return {
        "cost_per_input_token": round(input_per_m / 1_000_000, 12),
        "cost_per_output_token": round(output_per_m / 1_000_000, 12),
    }


MODEL_CAPABILITIES: dict[str, ModelCapability] = {
    # ---- OpenAI ----
    "gpt-4.1": _c("openai", "gpt-4.1", supports_tools=True, supports_vision=True,
                  max_context_tokens=1_000_000, latency_class="medium",
                  recommended_for=["investigation", "report", "critical"], **_per_m(2.5, 10)),
    "gpt-4.1-mini": _c("openai", "gpt-4.1-mini", supports_tools=True, supports_vision=True,
                       max_context_tokens=1_000_000, latency_class="fast",
                       recommended_for=["triage", "parsing", "enrichment"], **_per_m(0.15, 0.6)),
    "gpt-4o": _c("openai", "gpt-4o", supports_tools=True, supports_vision=True,
                 max_context_tokens=128_000, recommended_for=["investigation", "report"], **_per_m(2.5, 10)),
    "gpt-4o-mini": _c("openai", "gpt-4o-mini", supports_tools=True, supports_vision=True,
                      max_context_tokens=128_000, latency_class="fast",
                      recommended_for=["triage", "parsing"], **_per_m(0.15, 0.6)),
    # ---- Anthropic ----
    "claude-sonnet-4-6": _c("anthropic", "claude-sonnet-4-6", supports_tools=True, supports_vision=True,
                            max_context_tokens=200_000, recommended_for=["investigation", "report", "critical"],
                            **_per_m(3, 15)),
    "claude-opus-4-8": _c("anthropic", "claude-opus-4-8", supports_tools=True, supports_vision=True,
                          max_context_tokens=200_000, latency_class="slow",
                          recommended_for=["critical", "report"], **_per_m(15, 75)),
    # ---- Google ----
    "gemini-1.5-pro": _c("gemini", "gemini-1.5-pro", supports_tools=True, supports_vision=True,
                         max_context_tokens=2_000_000, recommended_for=["investigation"], **_per_m(1.25, 5)),
    # ---- Mistral / Cohere ----
    "mistral-large-latest": _c("mistral", "mistral-large-latest", supports_tools=True,
                               max_context_tokens=128_000, recommended_for=["investigation"], **_per_m(2, 6)),
    "command-r-plus": _c("cohere", "command-r-plus", supports_tools=True,
                         max_context_tokens=128_000, recommended_for=["investigation"], **_per_m(2.5, 10)),
    # ---- Groq (fast) ----
    "llama-3.1-70b-versatile": _c("groq", "llama-3.1-70b-versatile", supports_tools=True,
                                  max_context_tokens=131_072, latency_class="fast",
                                  recommended_for=["triage", "speed"], **_per_m(0.59, 0.79)),
    # ---- OpenRouter (gateway) ----
    "openai/gpt-4.1-mini": _c("openrouter", "openai/gpt-4.1-mini", supports_tools=True,
                              max_context_tokens=1_000_000, latency_class="fast",
                              recommended_for=["triage", "fallback"], **_per_m(0.15, 0.6)),
    # ---- Local models (zero cost, private) ----
    "llama3.1": _c("ollama", "llama3.1", supports_streaming=True, max_context_tokens=128_000,
                   privacy_level="local", latency_class="medium",
                   recommended_for=["privacy", "local", "investigation"]),
    "llama3.2": _c("ollama", "llama3.2", max_context_tokens=128_000, privacy_level="local",
                   latency_class="fast", recommended_for=["privacy", "triage"]),
    "qwen2.5": _c("ollama", "qwen2.5", max_context_tokens=32_768, privacy_level="local",
                  recommended_for=["privacy", "investigation"]),
    "mistral": _c("ollama", "mistral", max_context_tokens=32_768, privacy_level="local",
                  recommended_for=["privacy"]),
    "deepseek-r1-distill": _c("ollama", "deepseek-r1-distill", max_context_tokens=64_000,
                              privacy_level="local", latency_class="slow",
                              recommended_for=["privacy", "reasoning"]),
    "local-model": _c("generic_openai", "local-model", privacy_level="local",
                      recommended_for=["privacy", "local"]),
    # ---- Mock ----
    "mock-soc-1": _c("mock", "mock-soc-1", supports_json=True, supports_tools=False,
                     max_context_tokens=32_768, privacy_level="local", latency_class="fast",
                     recommended_for=["demo", "offline", "fallback"]),
}

# Default capability profiles per provider, used when a specific model is unknown.
PROVIDER_DEFAULT_PRIVACY = {
    "ollama": "local", "lmstudio": "local", "vllm": "local", "generic_openai": "local",
    "mock": "local",
}


def get_capability(model: str | None, provider: str | None = None) -> ModelCapability:
    """Return the capability for a model, falling back to a sensible default."""
    if model and model in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model]
    privacy = PROVIDER_DEFAULT_PRIVACY.get(provider or "", "external")
    return ModelCapability(
        provider=provider or "unknown",
        model=model or "unknown",
        privacy_level=privacy,
        cost_per_input_token=0.0 if privacy == "local" else 0.0000005,
        cost_per_output_token=0.0 if privacy == "local" else 0.0000015,
        recommended_for=["general"],
    )


def models_for_provider(provider: str) -> list[ModelCapability]:
    return [c for c in MODEL_CAPABILITIES.values() if c.provider == provider]


def all_capabilities() -> list[dict]:
    return [c.to_dict() for c in MODEL_CAPABILITIES.values()]


def estimate_cost_tokens(model: str, input_tokens: int, output_tokens: int,
                         provider: str | None = None) -> float:
    cap = get_capability(model, provider)
    return round(input_tokens * cap.cost_per_input_token + output_tokens * cap.cost_per_output_token, 6)


def supports(model: str, capability: str, provider: str | None = None) -> bool:
    cap = get_capability(model, provider)
    return bool(getattr(cap, capability, False))
