"""OpenAI provider (api.openai.com or any OpenAI base URL)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=model or settings.openai_model,
        )
