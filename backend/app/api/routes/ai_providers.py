"""AI provider management, health, observability and prompt preview routes."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.providers import LOCAL_PROVIDERS, PROVIDER_REGISTRY, build_provider
from app.ai.prompts import get_system_prompt, investigation_user_prompt, parser_user_prompt
from app.api.deps import get_context
from app.core.config import settings
from app.core.tenancy import TenantContext
from app.db.session import get_db
from app.models.ai import AIRun
from app.schemas import PromptPreviewRequest, ProviderTestRequest

router = APIRouter(prefix="/ai", tags=["ai"])

# Which env keys indicate a provider is configured.
CONFIG_KEYS = {
    "openai": lambda s: bool(s.openai_api_key),
    "azure_openai": lambda s: bool(s.azure_openai_api_key and s.azure_openai_endpoint),
    "anthropic": lambda s: bool(s.anthropic_api_key),
    "gemini": lambda s: bool(s.gemini_api_key),
    "mistral": lambda s: bool(s.mistral_api_key),
    "cohere": lambda s: bool(s.cohere_api_key),
    "groq": lambda s: bool(s.groq_api_key),
    "openrouter": lambda s: bool(s.openrouter_api_key),
    "generic_openai": lambda s: bool(s.generic_openai_base_url),
    "ollama": lambda s: bool(s.ollama_base_url),
    "lmstudio": lambda s: bool(s.lmstudio_base_url),
    "vllm": lambda s: bool(s.vllm_base_url),
    "mock": lambda s: True,
}

PROVIDER_MODELS = {
    "openai": lambda s: s.openai_model,
    "azure_openai": lambda s: s.azure_openai_deployment,
    "anthropic": lambda s: s.anthropic_model,
    "gemini": lambda s: s.gemini_model,
    "mistral": lambda s: s.mistral_model,
    "cohere": lambda s: s.cohere_model,
    "groq": lambda s: s.groq_model,
    "openrouter": lambda s: s.openrouter_model,
    "generic_openai": lambda s: s.generic_openai_model,
    "ollama": lambda s: s.ollama_model,
    "lmstudio": lambda s: s.lmstudio_model,
    "vllm": lambda s: s.vllm_model,
    "mock": lambda s: "mock-soc-1",
}


@router.get("/providers")
def list_providers(ctx: TenantContext = Depends(get_context)):
    out = []
    for key in PROVIDER_REGISTRY:
        out.append({
            "provider": key,
            "configured": CONFIG_KEYS.get(key, lambda s: False)(settings),
            "model": PROVIDER_MODELS.get(key, lambda s: None)(settings),
            "is_local": key in LOCAL_PROVIDERS,
            "cost_tracking": settings.ai_enable_cost_tracking,
            "is_default": key == settings.default_ai_provider,
        })
    return {
        "providers": out,
        "default_provider": settings.default_ai_provider,
        "default_model": settings.default_ai_model,
        "routing_mode": settings.ai_routing_mode,
        "fallback_chain": settings.fallback_chain_list,
        "fallback_enabled": settings.ai_enable_fallback,
        "pii_redaction": settings.ai_enable_pii_redaction,
        "strict_json": settings.ai_strict_json_mode,
    }


@router.get("/providers/health")
async def providers_health(ctx: TenantContext = Depends(get_context)):
    async def check(key: str):
        try:
            provider = build_provider(key)
            health = await provider.health_check()
            return {
                "provider": key, "configured": health.configured, "healthy": health.healthy,
                "is_local": health.is_local, "model": health.model, "detail": health.detail,
                "latency_ms": health.latency_ms,
            }
        except Exception as exc:  # noqa: BLE001
            return {"provider": key, "configured": False, "healthy": False,
                    "is_local": key in LOCAL_PROVIDERS, "detail": str(exc)[:120]}

    # Only health-check configured providers to avoid slow timeouts on unset ones.
    keys = [k for k in PROVIDER_REGISTRY if CONFIG_KEYS.get(k, lambda s: False)(settings)]
    results = await asyncio.gather(*[check(k) for k in keys])
    return {"results": list(results)}


@router.post("/providers/test")
async def test_provider(payload: ProviderTestRequest, ctx: TenantContext = Depends(get_context)):
    if payload.provider not in PROVIDER_REGISTRY:
        return {"provider": payload.provider, "ok": False, "detail": "unknown provider"}
    try:
        provider = build_provider(payload.provider, payload.model)
        health = await provider.health_check()
        return {"provider": payload.provider, "ok": health.healthy, "configured": health.configured,
                "model": health.model, "detail": health.detail, "latency_ms": health.latency_ms}
    except Exception as exc:  # noqa: BLE001
        return {"provider": payload.provider, "ok": False, "detail": str(exc)[:200]}


@router.get("/runs")
def list_runs(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context), limit: int = 20):
    rows = db.execute(
        select(AIRun).where(AIRun.organization_id == ctx.organization_id)
        .order_by(AIRun.created_at.desc()).limit(limit)
    ).scalars().all()
    return [
        {
            "id": r.id, "provider": r.provider, "model": r.model, "prompt_type": r.prompt_type,
            "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
            "estimated_cost": r.estimated_cost, "latency_ms": r.latency_ms, "success": r.success,
            "fallback_used": r.fallback_used, "is_local": r.is_local,
            "error_message": r.error_message, "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/usage-summary")
def usage_summary(db: Session = Depends(get_db), ctx: TenantContext = Depends(get_context)):
    org = ctx.organization_id
    base = select(AIRun).where(AIRun.organization_id == org)
    runs = db.execute(base).scalars().all()
    total = len(runs)
    failed = sum(1 for r in runs if not r.success)
    fallback = sum(1 for r in runs if r.fallback_used)
    local = sum(1 for r in runs if r.is_local)
    cloud = total - local
    input_tokens = sum(r.input_tokens for r in runs)
    output_tokens = sum(r.output_tokens for r in runs)
    cost = round(sum(r.estimated_cost for r in runs), 4)
    avg_latency = round(sum(r.latency_ms for r in runs) / total, 1) if total else 0

    by_provider: dict[str, int] = {}
    by_model: dict[str, int] = {}
    for r in runs:
        by_provider[r.provider] = by_provider.get(r.provider, 0) + 1
        if r.model:
            by_model[r.model] = by_model.get(r.model, 0) + 1
    most_used_model = max(by_model, key=by_model.get) if by_model else None

    return {
        "total_runs": total, "failed_requests": failed, "fallback_count": fallback,
        "local_requests": local, "cloud_requests": cloud, "input_tokens": input_tokens,
        "output_tokens": output_tokens, "estimated_cost": cost, "avg_latency_ms": avg_latency,
        "by_provider": by_provider, "by_model": by_model, "most_used_model": most_used_model,
        "active_provider": settings.default_ai_provider, "routing_mode": settings.ai_routing_mode,
        "fallback_chain": settings.fallback_chain_list,
    }


@router.post("/prompt-preview")
def prompt_preview(payload: PromptPreviewRequest, ctx: TenantContext = Depends(get_context)):
    system = get_system_prompt(payload.prompt_type)
    sample = payload.sample_text or "Multiple failed authentications from 203.0.113.10 for user jdoe."
    if payload.prompt_type == "alert_parser":
        user = parser_user_prompt(sample, "Generic")
    else:
        user = investigation_user_prompt({"alert_name": "Sample Alert", "raw_excerpt": sample})
    return {"prompt_type": payload.prompt_type, "system_prompt": system, "user_prompt": user}
