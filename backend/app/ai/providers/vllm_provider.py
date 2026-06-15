"""vLLM self-hosted provider (OpenAI-compatible server)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class VLLMProvider(OpenAICompatibleProvider):
    name = "vllm"
    is_local = True

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.generic_openai_api_key or "vllm",
            base_url=settings.vllm_base_url,
            model=model or settings.vllm_model,
        )
