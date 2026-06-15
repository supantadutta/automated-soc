"""AI provider registry."""
from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.azure_openai_provider import AzureOpenAIProvider
from app.ai.providers.cohere_provider import CohereProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.generic_openai_provider import GenericOpenAICompatibleProvider
from app.ai.providers.groq_provider import GroqProvider
from app.ai.providers.lmstudio_provider import LMStudioProvider
from app.ai.providers.mistral_provider import MistralProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.openrouter_provider import OpenRouterProvider
from app.ai.providers.vllm_provider import VLLMProvider

# provider key -> factory
PROVIDER_REGISTRY: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "azure_openai": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "mistral": MistralProvider,
    "cohere": CohereProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
    "generic_openai": GenericOpenAICompatibleProvider,
    "ollama": OllamaProvider,
    "lmstudio": LMStudioProvider,
    "vllm": VLLMProvider,
    "mock": MockAIProvider,
}

LOCAL_PROVIDERS = {"ollama", "lmstudio", "vllm", "mock", "generic_openai"}


def build_provider(key: str, model: str | None = None) -> AIProvider:
    cls = PROVIDER_REGISTRY.get(key)
    if cls is None:
        raise ValueError(f"unknown provider: {key}")
    return cls(model=model)  # type: ignore[call-arg]


__all__ = [
    "PROVIDER_REGISTRY",
    "LOCAL_PROVIDERS",
    "build_provider",
    "AIProvider",
    "MockAIProvider",
]
