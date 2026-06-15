# mitre_mapping

**System:** guardrails + "You map observed activity to MITRE ATT&CK tactics and techniques."

**User:** the alert category and observed behaviour. The model returns an array of:
```json
[{ "tactic": "Command and Control", "technique": "Application Layer Protocol",
   "technique_id": "T1071", "confidence": 60, "reason": "Periodic TLS beaconing to a known-bad domain." }]
```
Confidence reflects how well the evidence supports the mapping; rationale is required for each entry.
