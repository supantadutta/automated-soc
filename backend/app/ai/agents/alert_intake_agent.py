"""Alert Intake Agent — parses raw alerts and detects category.

Uses the deterministic parser service first (reliable, offline) and optionally
an AI parse for messy free-text alerts.
"""
from __future__ import annotations

from typing import Any

from app.ai.agents.base import AgentContext, BaseAgent
from app.ai.base import extract_json
from app.ai.prompts import get_system_prompt, parser_user_prompt
from app.ai.schemas import AIRequest


class AlertIntakeAgent(BaseAgent):
    name = "alert_intake_agent"

    async def parse_with_ai(
        self, raw: str, source_tool: str | None, ctx: AgentContext
    ) -> dict[str, Any]:
        request = AIRequest.simple(
            system=get_system_prompt("alert_parser"),
            user=parser_user_prompt(raw, source_tool),
            json_mode=True,
            prompt_type="alert_parser",
            metadata={"parsed_hint": {}},
        )
        route = await self._run(request, ctx)
        try:
            return extract_json(route.response.text)
        except Exception:
            return {}
