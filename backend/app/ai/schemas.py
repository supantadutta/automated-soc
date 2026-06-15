"""Shared AI request/response data structures and the investigation JSON schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AIMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class AIRequest:
    messages: list[AIMessage]
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout: int = 60
    json_mode: bool = False
    prompt_type: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def simple(cls, system: str, user: str, **kwargs) -> "AIRequest":
        return cls(
            messages=[AIMessage("system", system), AIMessage("user", user)], **kwargs
        )

    def to_openai_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class AIResponse:
    text: str
    provider: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: int = 0
    estimated_cost: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None


@dataclass
class ProviderHealth:
    provider: str
    configured: bool
    healthy: bool
    is_local: bool
    model: Optional[str] = None
    detail: Optional[str] = None
    latency_ms: Optional[int] = None


@dataclass
class CostEstimate:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    currency: str = "USD"


class AIProviderError(Exception):
    """Normalized provider error. Never carries raw secrets."""

    def __init__(self, provider: str, message: str, status: Optional[int] = None):
        self.provider = provider
        self.status = status
        super().__init__(f"[{provider}] {message}")


# --- Canonical investigation output JSON schema ---------------------------------
INVESTIGATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "technical_analysis": {"type": "string"},
        "verdict": {
            "type": "string",
            "enum": [
                "True Positive",
                "False Positive",
                "Benign Authorized Activity",
                "Duplicate",
                "Needs Review",
                "Escalated",
            ],
        },
        "confidence_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "severity_recommendation": {
            "type": "string",
            "enum": ["Informational", "Low", "Medium", "High", "Critical"],
        },
        "reasoning_summary": {"type": "string"},
        "facts_observed": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array"},
        "missing_evidence": {"type": "array", "items": {"type": "string"}},
        "ioc_summary": {"type": "array"},
        "mitre_mapping": {"type": "array"},
        "timeline": {"type": "array"},
        "recommended_actions": {"type": "array"},
        "customer_email_draft": {"type": "string"},
        "ticket_update": {"type": "string"},
        "investigation_checklist": {"type": "array", "items": {"type": "string"}},
        "detection_query_suggestions": {"type": "object"},
        "qa_warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "confidence_score", "executive_summary"],
}


def empty_investigation() -> dict[str, Any]:
    """A structurally valid, conservative default investigation result."""
    return {
        "executive_summary": "",
        "technical_analysis": "",
        "verdict": "Needs Review",
        "confidence_score": 0,
        "severity_recommendation": "Medium",
        "reasoning_summary": "",
        "false_positive_reasoning": "",
        "facts_observed": [],
        "assumptions": [],
        "evidence": [],
        "missing_evidence": [],
        "ioc_summary": [],
        "mitre_mapping": [],
        "timeline": [],
        "recommended_actions": [],
        "customer_email_draft": "",
        "ticket_update": "",
        "investigation_checklist": [],
        "detection_query_suggestions": {
            "splunk": "",
            "crowdstrike_logscale": "",
            "wazuh": "",
            "elastic_kql": "",
            "sigma": "",
            "sentinel_kql": "",
        },
        "qa_warnings": [],
    }
