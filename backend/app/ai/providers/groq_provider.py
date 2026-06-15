"""Groq provider (OpenAI-compatible, very fast)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=model or settings.groq_model,
        )
