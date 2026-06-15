"""Mistral provider (OpenAI-compatible chat completions API)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class MistralProvider(OpenAICompatibleProvider):
    name = "mistral"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.mistral_api_key,
            base_url="https://api.mistral.ai/v1",
            model=model or settings.mistral_model,
        )
