"""Generic OpenAI-compatible provider for any self-hosted/3rd-party endpoint
(DeepSeek, Together AI, Fireworks, custom gateways, etc.)."""
from __future__ import annotations

from app.ai.providers._openai_compatible import OpenAICompatibleProvider
from app.core.config import settings


class GenericOpenAICompatibleProvider(OpenAICompatibleProvider):
    name = "generic_openai"
    is_local = False

    def __init__(self, model: str | None = None):
        super().__init__(
            api_key=settings.generic_openai_api_key,
            base_url=settings.generic_openai_base_url,
            model=model or settings.generic_openai_model,
        )
