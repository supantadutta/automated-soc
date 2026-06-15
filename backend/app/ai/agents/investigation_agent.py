"""Investigation Agent — determines verdict, confidence, evidence and missing
evidence by calling the routed AI provider with the SOC investigation prompt.

Implements structured-output reliability: lenient parse → JSON repair →
schema coercion → one stricter retry on invalid output → completeness QA. If
every attempt fails the router's mock fallback still yields a valid structure.
"""
from __future__ import annotations

from typing import Any

from app.ai.agents.base import AgentContext, BaseAgent
from app.ai.prompts import get_system_prompt, investigation_user_prompt
from app.ai.schemas import AIRequest
from app.ai.validation import (
    coerce_investigation,
    completeness_warnings,
    is_valid_investigation,
    parse_json_lenient,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.investigation_agent")

_STRICTER_SUFFIX = (
    "\n\nIMPORTANT: Your previous response was not valid JSON or was missing "
    "required fields. Respond with ONE strict JSON object only — no prose, no "
    "markdown fences — including at minimum: verdict, confidence_score, "
    "executive_summary, evidence, missing_evidence."
)


class InvestigationAgent(BaseAgent):
    name = "investigation_agent"

    async def investigate(self, context: dict[str, Any], ctx: AgentContext) -> dict[str, Any]:
        base_user = investigation_user_prompt(context)
        route = await self._call(base_user, context, ctx)
        data = parse_json_lenient(route.response.text)

        # Retry once with a stricter instruction if the output was unusable.
        retried = False
        if not is_valid_investigation(data):
            logger.info("investigation output invalid; retrying with stricter prompt")
            retried = True
            route = await self._call(base_user + _STRICTER_SUFFIX, context, ctx)
            data = parse_json_lenient(route.response.text)

        result = coerce_investigation(data or {})

        # Completeness QA — incomplete output adds warnings and caps confidence.
        warnings = completeness_warnings(result)
        if data is None:
            warnings.append("AI response was not valid JSON; defaulted to a conservative result.")
        if warnings:
            result["qa_warnings"] = list(dict.fromkeys((result.get("qa_warnings") or []) + warnings))
            if result.get("verdict") in {"True Positive", "False Positive"}:
                result["verdict"] = "Needs Review"
                result["confidence_score"] = min(result.get("confidence_score", 0) or 0, 45)

        result["_provider"] = route.provider
        result["_model"] = route.model
        result["_fallback_used"] = route.fallback_used or retried
        result["_pii_redacted"] = route.pii_redacted
        result["_retried"] = retried
        return result

    async def _call(self, user_prompt: str, context: dict[str, Any], ctx: AgentContext):
        request = AIRequest.simple(
            system=get_system_prompt("soc_investigation"),
            user=user_prompt,
            json_mode=settings.ai_strict_json_mode,
            prompt_type="soc_investigation",
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            metadata=context,
        )
        return await self._run(request, ctx)
