"""SOC prompt templates.

Hard rules embedded in every analytical prompt:
  - Evidence-based wording only.
  - Never claim compromise without evidence; never claim false positive without evidence.
  - Separate facts, assumptions and missing evidence.
  - Always include a confidence score and next validation steps.
  - Return strict JSON for backend processing.
  - Never output destructive commands as automatic actions; response actions are
    recommendation-only and flagged for human approval.
"""
from __future__ import annotations

import json
from typing import Any

from app.ai.schemas import INVESTIGATION_JSON_SCHEMA

SOC_GUARDRAILS = """You are a senior SOC (Security Operations Center) analyst assistant for a
DEFENSIVE cybersecurity platform. Follow these rules strictly:
- Base every conclusion on the evidence provided. Do not invent indicators.
- Never assert a compromise (True Positive) without supporting evidence.
- Never assert a False Positive without supporting evidence.
- Clearly separate FACTS, ASSUMPTIONS and MISSING EVIDENCE.
- Always include a confidence score (0-100) and concrete next validation steps.
- If evidence is weak or contradictory, set verdict to "Needs Review".
- Response/containment actions are RECOMMENDATIONS ONLY and must be flagged
  requires_human_approval=true. Never produce destructive automation.
- Use professional, concise SOC language. Provide a reasoning summary, never a
  hidden chain-of-thought.
- Output MUST be a single strict JSON object with no markdown fences."""

SYSTEM_PROMPTS: dict[str, str] = {
    "alert_parser": (
        SOC_GUARDRAILS
        + "\nYou parse a raw security alert and extract normalized fields as JSON."
    ),
    "soc_investigation": SOC_GUARDRAILS,
    "mitre_mapping": (
        SOC_GUARDRAILS
        + "\nYou map observed activity to MITRE ATT&CK tactics and techniques."
    ),
    "report_writer": (
        SOC_GUARDRAILS
        + "\nYou write a professional SOC investigation report in markdown."
    ),
    "customer_email_prompt": (
        SOC_GUARDRAILS
        + "\nYou draft a clear, professional customer-facing notification email."
    ),
    "ticket_note_prompt": (
        SOC_GUARDRAILS + "\nYou write a concise ticketing-system update note."
    ),
    "detection_query_prompt": (
        SOC_GUARDRAILS
        + "\nYou write detection queries (Splunk SPL, CrowdStrike LogScale, Wazuh,"
        " Elastic KQL, Sigma, Sentinel KQL)."
    ),
    "qa_review_prompt": (
        SOC_GUARDRAILS
        + "\nYou QA-review another analyst's AI output. Flag weak claims, missing"
        " evidence and hallucination risk. Force 'Needs Review' if evidence is weak."
    ),
    "executive_summary_prompt": (
        SOC_GUARDRAILS + "\nYou write a 3-5 sentence executive summary."
    ),
    "false_positive_analysis_prompt": (
        SOC_GUARDRAILS
        + "\nYou assess whether the alert is a likely false positive, citing evidence."
    ),
}


def investigation_user_prompt(context: dict[str, Any]) -> str:
    schema = json.dumps(INVESTIGATION_JSON_SCHEMA, indent=2)
    ctx = json.dumps(context, indent=2, default=str)
    return f"""Investigate the following SOC alert and supporting context.

=== ALERT & CONTEXT (JSON) ===
{ctx}

=== REQUIRED OUTPUT ===
Return a single JSON object that conforms to this schema:
{schema}

Remember: evidence-based only, separate facts/assumptions/missing evidence,
include confidence_score, set verdict to "Needs Review" if evidence is weak, and
mark every recommended action requires_human_approval=true unless trivially safe
(read-only validation)."""


def parser_user_prompt(raw: str, source_tool: str | None) -> str:
    return f"""Parse this raw alert from source tool '{source_tool or 'unknown'}'.
Extract these fields as a JSON object (use null when absent):
alert_name, source_tool, severity, event_time, src_ip, dest_ip, username,
hostname, domain, url, file_hash, process_name, command_line, category.

category must be one of: brute_force, password_spray, suspicious_auth,
unusual_login, new_endpoint, rdp_anomaly, ssh_brute_force, powershell, malware,
credential_dumping, dll_injection, directory_traversal, sql_injection, xss,
waf_attack, dns, dns_tunneling, c2, lateral_movement, generic.

=== RAW ALERT ===
{raw}"""


def qa_user_prompt(investigation_result: dict[str, Any]) -> str:
    payload = json.dumps(investigation_result, indent=2, default=str)
    return f"""Review this AI investigation result for quality and safety.
Return JSON: {{"qa_warnings": [string], "force_needs_review": bool, "passed": bool}}.
Flag: unsupported TP/FP claims, high confidence with major missing evidence,
hallucinated indicators, or destructive auto-actions.

=== INVESTIGATION RESULT ===
{payload}"""


def get_system_prompt(prompt_type: str) -> str:
    return SYSTEM_PROMPTS.get(prompt_type, SOC_GUARDRAILS)
