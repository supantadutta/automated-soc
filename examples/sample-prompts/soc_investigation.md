# soc_investigation

**System:** the shared SOC guardrails.

**User:** the normalized alert + enrichment + correlation + customer context as JSON, plus the full investigation output JSON schema (executive_summary, technical_analysis, verdict, confidence_score, evidence, missing_evidence, ioc_summary, mitre_mapping, timeline, recommended_actions, detection_query_suggestions, qa_warnings, ...).

The model must:
- Separate facts, assumptions, and missing evidence.
- Set verdict to "Needs Review" when evidence is weak.
- Mark every recommended action `requires_human_approval=true` unless it is read-only validation.
- Return a single strict JSON object.

See the schema in `docs/api.md` → "Investigation result schema".
