"""AIRouter: provider selection, fallback chain, privacy enforcement and
observability.

Routing modes:
  auto         - default chain from settings
  cost         - cheapest/local first, escalate on failure
  quality      - highest-quality configured provider first
  privacy      - local-only providers, never call external APIs
  speed        - fastest healthy provider (groq/local) first
  soc_critical - best model + mandatory QA review + strict JSON
  offline      - mock provider only

Per-customer policy can force local_only_mode / disallow external AI and request
PII redaction before any external call.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.capabilities import get_capability, models_for_provider
from app.ai.providers import LOCAL_PROVIDERS, build_provider
from app.ai.schemas import AIProviderError, AIRequest, AIResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.redaction import redact_pii

logger = get_logger("ai.router")

QUALITY_ORDER = ["anthropic", "openai", "azure_openai", "gemini", "mistral", "openrouter", "groq", "ollama", "mock"]
COST_ORDER = ["mock", "ollama", "lmstudio", "vllm", "groq", "openai", "anthropic"]
SPEED_ORDER = ["groq", "ollama", "lmstudio", "openai", "mock"]

# Public routing policy names (and their internal mode). Both forms are accepted.
ROUTING_POLICIES = {
    "auto": "auto",
    "cost_optimized": "cost",
    "quality_optimized": "quality",
    "privacy_optimized": "privacy",
    "local_only": "privacy",
    "speed_optimized": "speed",
    "critical_alert_mode": "soc_critical",
    "offline_demo": "offline",
    # internal short forms (back-compat)
    "cost": "cost", "quality": "quality", "privacy": "privacy",
    "speed": "speed", "soc_critical": "soc_critical", "offline": "offline",
}


def normalize_mode(mode: str | None) -> str:
    return ROUTING_POLICIES.get((mode or "auto").lower(), "auto")


def select_model(provider: str, mode: str, requested: str | None = None) -> str | None:
    """Capability-aware model selection for a provider given the routing mode.

    Honors an explicit request, otherwise picks a model from the capability
    registry whose ``recommended_for`` matches the routing intent.
    """
    if requested:
        return requested
    candidates = models_for_provider(provider)
    if not candidates:
        return None
    intent = {
        "cost": "triage", "speed": "speed", "quality": "investigation",
        "soc_critical": "critical", "privacy": "privacy", "offline": "demo",
    }.get(mode, "investigation")
    matches = [c for c in candidates if intent in c.recommended_for]
    pool = matches or candidates
    # For cost/speed prefer cheaper/faster; for quality/critical prefer pricier.
    if mode in {"cost", "speed"}:
        pool.sort(key=lambda c: (c.cost_per_output_token, c.latency_class != "fast"))
    elif mode in {"quality", "soc_critical"}:
        pool.sort(key=lambda c: -c.cost_per_output_token)
    return pool[0].model


@dataclass
class CustomerPolicy:
    external_ai_allowed: bool = True
    preferred_provider: Optional[str] = None
    fallback_allowed: bool = True
    redact_pii_before_ai: bool = True
    store_ai_outputs: bool = True
    local_only_mode: bool = False

    @classmethod
    def from_model(cls, policy) -> "CustomerPolicy":
        if policy is None:
            return cls()
        return cls(
            external_ai_allowed=policy.external_ai_allowed,
            preferred_provider=policy.preferred_provider,
            fallback_allowed=policy.fallback_allowed,
            redact_pii_before_ai=policy.redact_pii_before_ai,
            store_ai_outputs=policy.store_ai_outputs,
            local_only_mode=policy.local_only_mode,
        )


@dataclass
class RouteResult:
    response: AIResponse
    provider: str
    model: str
    fallback_used: bool
    chain_attempted: list[str] = field(default_factory=list)
    pii_redacted: bool = False


class AIRouter:
    def __init__(self, mode: str | None = None):
        self.mode = normalize_mode(mode or settings.ai_routing_mode)

    # ----------------------------------------------------------- chain building
    def build_chain(self, policy: CustomerPolicy, override_provider: str | None = None) -> list[str]:
        if override_provider and override_provider not in {"auto", ""}:
            chain = [override_provider]
            if policy.fallback_allowed and settings.ai_enable_fallback:
                chain += [p for p in settings.fallback_chain_list if p != override_provider]
            return self._apply_policy(chain, policy)

        if self.mode == "offline":
            return ["mock"]
        if self.mode == "privacy":
            return self._local_only_chain(policy)
        if self.mode == "quality":
            chain = list(QUALITY_ORDER)
        elif self.mode == "cost":
            chain = list(COST_ORDER)
        elif self.mode == "speed":
            chain = list(SPEED_ORDER)
        elif self.mode == "soc_critical":
            chain = list(QUALITY_ORDER)
        else:  # auto
            chain = [settings.default_ai_provider] + settings.fallback_chain_list

        if policy.preferred_provider:
            chain = [policy.preferred_provider] + [c for c in chain if c != policy.preferred_provider]
        return self._apply_policy(chain, policy)

    def _local_only_chain(self, policy: CustomerPolicy) -> list[str]:
        preferred = [policy.preferred_provider] if policy.preferred_provider in LOCAL_PROVIDERS else []
        base = preferred + ["ollama", "lmstudio", "vllm", "mock"]
        return list(dict.fromkeys(base))

    def _apply_policy(self, chain: list[str], policy: CustomerPolicy) -> list[str]:
        # Enforce local-only / external-not-allowed by filtering out cloud providers.
        if policy.local_only_mode or not policy.external_ai_allowed:
            chain = [c for c in chain if c in LOCAL_PROVIDERS]
            if not chain:
                chain = ["mock"]
        # De-dup, always guarantee mock as final safety net.
        chain = list(dict.fromkeys(chain))
        if "mock" not in chain:
            chain.append("mock")
        if not policy.fallback_allowed:
            # Keep only the first real choice plus mock fallback safety net.
            chain = [chain[0], "mock"] if chain[0] != "mock" else ["mock"]
        return chain

    # --------------------------------------------------------------------- run
    async def run(
        self,
        request: AIRequest,
        *,
        policy: CustomerPolicy | None = None,
        override_provider: str | None = None,
        db: Session | None = None,
        organization_id: int | None = None,
        customer_id: int | None = None,
        alert_id: int | None = None,
        investigation_id: int | None = None,
        created_by: int | None = None,
    ) -> RouteResult:
        policy = policy or CustomerPolicy()
        chain = self.build_chain(policy, override_provider)
        attempted: list[str] = []
        pii_redacted = False

        for idx, provider_key in enumerate(chain):
            is_external = provider_key not in LOCAL_PROVIDERS
            req = request

            # Privacy Guard: redact PII/secrets before any external provider call.
            if is_external and (policy.redact_pii_before_ai or settings.ai_enable_pii_redaction):
                req = self._redact_request(request)
                pii_redacted = True

            attempted.append(provider_key)
            started = time.perf_counter()
            try:
                # Capability-aware model selection: honor an explicit model on the
                # first hop, otherwise pick a model that suits the routing intent.
                requested_model = request.model if idx == 0 else None
                model = select_model(provider_key, self.mode, requested_model)
                provider = build_provider(provider_key, model)
                response = await provider.generate(req)
                self._record(
                    db, response, success=True, fallback_used=idx > 0,
                    is_local=provider_key in LOCAL_PROVIDERS, prompt_type=request.prompt_type,
                    organization_id=organization_id, customer_id=customer_id,
                    alert_id=alert_id, investigation_id=investigation_id, created_by=created_by,
                )
                return RouteResult(
                    response=response, provider=provider_key, model=response.model,
                    fallback_used=idx > 0, chain_attempted=attempted, pii_redacted=pii_redacted,
                )
            except Exception as exc:  # noqa: BLE001 - normalize & continue chain
                latency = int((time.perf_counter() - started) * 1000)
                msg = exc.provider_message if isinstance(exc, AIProviderError) else str(exc)
                logger.warning("provider %s failed: %s", provider_key, msg)
                self._record_failure(
                    db, provider_key, msg, latency, request.prompt_type,
                    organization_id, customer_id, alert_id, investigation_id, created_by,
                )
                continue

        raise AIProviderError("router", "all providers in chain failed")

    # --------------------------------------------------------------- internals
    def _redact_request(self, request: AIRequest) -> AIRequest:
        from app.ai.schemas import AIMessage

        return AIRequest(
            messages=[AIMessage(m.role, redact_pii(m.content)) for m in request.messages],
            model=request.model, temperature=request.temperature,
            max_tokens=request.max_tokens, timeout=request.timeout,
            json_mode=request.json_mode, prompt_type=request.prompt_type,
            metadata=request.metadata,
        )

    def _record(self, db, response, *, success, fallback_used, is_local, prompt_type,
                organization_id, customer_id, alert_id, investigation_id, created_by):
        if db is None or organization_id is None or not settings.ai_enable_cost_tracking:
            return
        from app.models.ai import AIRun

        db.add(AIRun(
            organization_id=organization_id, customer_id=customer_id, alert_id=alert_id,
            investigation_id=investigation_id, provider=response.provider, model=response.model,
            prompt_type=prompt_type, input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens, estimated_cost=response.estimated_cost,
            latency_ms=response.latency_ms, success=success, fallback_used=fallback_used,
            is_local=is_local, created_by=created_by,
        ))
        db.commit()

    def _record_failure(self, db, provider_key, message, latency, prompt_type,
                        organization_id, customer_id, alert_id, investigation_id, created_by):
        if db is None or organization_id is None or not settings.ai_enable_cost_tracking:
            return
        from app.models.ai import AIRun
        from app.core.logging import redact_secrets

        db.add(AIRun(
            organization_id=organization_id, customer_id=customer_id, alert_id=alert_id,
            investigation_id=investigation_id, provider=provider_key, model=None,
            prompt_type=prompt_type, latency_ms=latency, success=False,
            error_message=redact_secrets(message)[:500], fallback_used=True,
            is_local=provider_key in LOCAL_PROVIDERS, created_by=created_by,
        ))
        db.commit()


# AIProviderError convenience attribute used above.
def _provider_message(self):  # pragma: no cover
    return str(self)


AIProviderError.provider_message = property(_provider_message)  # type: ignore[attr-defined]
