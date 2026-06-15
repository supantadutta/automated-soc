"""LM Studio local provider (OpenAI-compatible server at /v1)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class LMStudioProvider(OpenAICompatibleProvider):
    name = "lmstudio"
    is_local = True

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key="lm-studio",  # LM Studio ignores the key
            base_url=settings.lmstudio_base_url,
            model=model or settings.lmstudio_model,
        )
