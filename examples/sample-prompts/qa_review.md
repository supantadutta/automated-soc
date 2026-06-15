# qa_review

**System:** guardrails + "You QA-review another analyst's AI output. Flag weak claims, missing evidence and hallucination risk. Force 'Needs Review' if evidence is weak."

**User:** the investigation result JSON.

**Expected JSON:**
```json
{ "qa_warnings": ["Verdict asserts TP/FP but no supporting evidence is listed."],
  "force_needs_review": true, "passed": false }
```

The QA agent also runs deterministic checks (unsupported TP/FP, high confidence with major missing evidence, destructive actions not flagged for approval) independent of the LLM.
