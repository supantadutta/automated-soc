"""Investigation Agent — determines verdict, confidence, evidence and missing
evidence by calling the routed AI provider with the SOC investigation prompt."""
from __future__ import annotations

from typing import Any

from app.ai.agents.base import AgentContext, BaseAgent
from app.ai.base import extract_json
from app.ai.prompts import get_system_prompt, investigation_user_prompt
from app.ai.schemas import AIRequest, empty_investigation
from app.core.config import settings


class InvestigationAgent(BaseAgent):
    name = "investigation_agent"

    async def investigate(self, context: dict[str, Any], ctx: AgentContext) -> dict[str, Any]:
        request = AIRequest.simple(
            system=get_system_prompt("soc_investigation"),
            user=investigation_user_prompt(context),
            json_mode=settings.ai_strict_json_mode,
            prompt_type="soc_investigation",
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            metadata=context,
        )
        result_route = await self._run(request, ctx)
        try:
            data = extract_json(result_route.response.text)
        except Exception:
            data = empty_investigation()
            data["qa_warnings"] = ["AI response was not valid JSON; defaulted to Needs Review."]

        base = empty_investigation()
        base.update({k: v for k, v in data.items() if v is not None})
        base["_provider"] = result_route.provider
        base["_model"] = result_route.model
        base["_fallback_used"] = result_route.fallback_used
        base["_pii_redacted"] = result_route.pii_redacted
        return base
