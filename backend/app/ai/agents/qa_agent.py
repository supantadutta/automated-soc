"""QA Review Agent — reviews investigation output and enforces conservative
verdicts. Combines deterministic checks with an optional AI QA pass."""
from __future__ import annotations

from typing import Any

from app.ai.agents.base import AgentContext, BaseAgent
from app.ai.base import extract_json
from app.ai.prompts import get_system_prompt, qa_user_prompt
from app.ai.schemas import AIRequest


class QAReviewAgent(BaseAgent):
    name = "qa_agent"

    def deterministic_checks(self, result: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        verdict = result.get("verdict")
        evidence = result.get("evidence") or []
        missing = result.get("missing_evidence") or []
        confidence = result.get("confidence_score", 0) or 0

        if verdict in {"True Positive", "False Positive"} and not evidence:
            warnings.append(f"Verdict '{verdict}' asserted without listed evidence.")
        if confidence >= 80 and len(missing) >= 3:
            warnings.append("High confidence despite significant missing evidence.")
        if verdict == "True Positive" and confidence < 50:
            warnings.append("True Positive verdict with low confidence — verify before escalation.")
        for action in result.get("recommended_actions") or []:
            if isinstance(action, dict) and not action.get("requires_human_approval", True):
                txt = (action.get("action") or "").lower()
                if any(k in txt for k in ["delete", "disable", "block", "kill", "isolate", "remove"]):
                    warnings.append("Potentially destructive action not flagged for human approval.")
        return warnings

    async def review(
        self, result: dict[str, Any], ctx: AgentContext, use_ai: bool = False
    ) -> dict[str, Any]:
        warnings = self.deterministic_checks(result)
        force_needs_review = False

        if use_ai:
            request = AIRequest.simple(
                system=get_system_prompt("qa_review_prompt"),
                user=qa_user_prompt(result),
                json_mode=True,
                prompt_type="qa_review",
                metadata={"investigation_result": result},
            )
            try:
                route = await self._run(request, ctx)
                ai_qa = extract_json(route.response.text)
                warnings += [w for w in ai_qa.get("qa_warnings", []) if w not in warnings]
                force_needs_review = bool(ai_qa.get("force_needs_review"))
            except Exception:
                pass

        # Enforce conservative verdict if evidence is weak.
        if (force_needs_review or warnings) and result.get("verdict") in {
            "True Positive",
            "False Positive",
        }:
            evidence = result.get("evidence") or []
            if len(evidence) < 1 or force_needs_review:
                result["verdict"] = "Needs Review"
                result["confidence_score"] = min(result.get("confidence_score", 0) or 0, 45)
                warnings.append("Verdict downgraded to 'Needs Review' by QA enforcement.")

        result["qa_warnings"] = list(dict.fromkeys((result.get("qa_warnings") or []) + warnings))
        return result
