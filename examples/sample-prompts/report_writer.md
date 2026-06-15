# report_writer

**System:** guardrails + "You write a professional SOC investigation report in markdown."

The Report Writer agent renders a deterministic markdown report from the structured investigation result with the 17 required sections (Executive Summary → Analyst Feedback), so reports are consistent and always evidence-based. An LLM may be used to enrich prose, but the section structure and the "all response actions require human approval" banner are always enforced.

See `examples/sample-reports/` for rendered output.
