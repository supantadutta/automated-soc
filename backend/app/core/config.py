"""Application configuration loaded from environment variables.

All secrets (API keys, DB credentials) are read from the environment and are
never exposed to the frontend. See docs/security.md for the full secrets policy.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- App ---
    app_name: str = "AutoSOC Command Center"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = Field(default="")
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    # --- Security / Auth ---
    jwt_secret: str = Field(default="change-me-in-production-please-32-bytes-min")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    seed_admin_email: str = Field(default="admin@autosoc.local")
    seed_admin_password: str = Field(default="Admin123!")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg2://autosoc:autosoc@localhost:5432/autosoc"
    )

    # --- Redis / Celery ---
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # --- Vector memory ---
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_collection: str = Field(default="autosoc_memory")
    vector_backend: str = Field(default="memory")  # memory | qdrant | pgvector

    # --- AI routing ---
    default_ai_provider: str = Field(default="mock")
    default_ai_model: str = Field(default="mock-soc-1")
    ai_fallback_chain: str = Field(default="mock")
    ai_routing_mode: str = Field(default="auto")  # auto|cost|quality|privacy|speed|soc_critical|offline
    ai_strict_json_mode: bool = Field(default=True)
    ai_enable_fallback: bool = Field(default=True)
    ai_enable_cost_tracking: bool = Field(default=True)
    ai_enable_output_qa: bool = Field(default=True)
    ai_enable_pii_redaction: bool = Field(default=True)
    ai_request_timeout: int = Field(default=60)
    ai_max_tokens: int = Field(default=2048)
    ai_temperature: float = Field(default=0.2)

    # --- Provider credentials ---
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4.1-mini")
    openai_base_url: str = Field(default="https://api.openai.com/v1")

    azure_openai_api_key: str = Field(default="")
    azure_openai_endpoint: str = Field(default="")
    azure_openai_deployment: str = Field(default="")
    azure_openai_api_version: str = Field(default="2024-06-01")

    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-sonnet-4-6")
    anthropic_base_url: str = Field(default="https://api.anthropic.com/v1")

    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-pro")

    mistral_api_key: str = Field(default="")
    mistral_model: str = Field(default="mistral-large-latest")

    cohere_api_key: str = Field(default="")
    cohere_model: str = Field(default="command-r-plus")

    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.1-70b-versatile")

    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="openai/gpt-4.1-mini")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")

    generic_openai_base_url: str = Field(default="")
    generic_openai_api_key: str = Field(default="")
    generic_openai_model: str = Field(default="local-model")

    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1")

    lmstudio_base_url: str = Field(default="http://localhost:1234/v1")
    lmstudio_model: str = Field(default="local-model")

    vllm_base_url: str = Field(default="http://localhost:8001/v1")
    vllm_model: str = Field(default="local-model")

    # --- Enrichment provider keys (optional) ---
    virustotal_api_key: str = Field(default="")
    abuseipdb_api_key: str = Field(default="")
    otx_api_key: str = Field(default="")
    greynoise_api_key: str = Field(default="")
    shodan_api_key: str = Field(default="")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def fallback_chain_list(self) -> List[str]:
        return [p.strip() for p in self.ai_fallback_chain.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
