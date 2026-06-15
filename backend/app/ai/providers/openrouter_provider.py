"""OpenRouter provider (OpenAI-compatible gateway to many models)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=model or settings.openrouter_model,
            extra_headers={
                "HTTP-Referer": "https://autosoc.local",
                "X-Title": "AutoSOC Command Center",
            },
        )
