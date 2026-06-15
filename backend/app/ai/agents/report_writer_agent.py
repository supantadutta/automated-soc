"""Report Writer Agent — renders a professional markdown SOC report from the
structured investigation result. Deterministic so reports are consistent and
always include the required sections."""
from __future__ import annotations

from typing import Any


class ReportWriterAgent:
    name = "report_writer_agent"

    def render_markdown(
        self,
        alert: dict[str, Any],
        normalized: dict[str, Any],
        investigation: dict[str, Any],
        correlation: dict[str, Any] | None = None,
    ) -> str:
        correlation = correlation or {}
        inv = investigation
        lines: list[str] = []
        a = lines.append

        a(f"# SOC Investigation Report — {alert.get('title', 'Alert')}")
        a("")
        a(f"- **Verdict:** {inv.get('verdict', 'Needs Review')}")
        a(f"- **Confidence:** {inv.get('confidence_score', 0)}%")
        a(f"- **Recommended Severity:** {inv.get('severity_recommendation', 'Medium')}")
        a(f"- **Source Tool:** {alert.get('source_tool', 'N/A')}")
        a(f"- **AI Provider/Model:** {inv.get('_provider', 'mock')}/{inv.get('_model', 'mock-soc-1')}")
        a("")

        a("## 1. Executive Summary")
        a(inv.get("executive_summary", "") or "_Not available._")
        a("")
        a("## 2. Alert Overview")
        a(f"- **Title:** {alert.get('title', '')}")
        a(f"- **Severity (reported):** {alert.get('severity', '')}")
        a(f"- **Category:** {alert.get('category', 'generic')}")
        a("")
        a("## 3. Technical Analysis")
        a(inv.get("technical_analysis", "") or "_Not available._")
        a("")
        a("## 4. Affected Entities")
        for label, key in [("Source IP", "src_ip"), ("Destination IP", "dest_ip"),
                           ("Username", "username"), ("Hostname", "hostname"),
                           ("Domain", "domain"), ("File Hash", "file_hash")]:
            if normalized.get(key):
                a(f"- **{label}:** {normalized[key]}")
        a("")
        a("## 5. IOC Enrichment")
        ioc_summary = inv.get("ioc_summary") or []
        if ioc_summary:
            a("| IOC | Type | Reputation | Risk | Sources |")
            a("|-----|------|------------|------|---------|")
            for i in ioc_summary:
                a(f"| {i.get('value','')} | {i.get('ioc_type','')} | {i.get('reputation','')} | {i.get('risk_score',0)} | {', '.join(i.get('sources', []))} |")
        else:
            a("_No IOC enrichment results available._")
        a("")
        a("## 6. Case Correlation")
        if correlation.get("matches"):
            for m in correlation["matches"]:
                a(f"- {m.get('reason', '')} (alert #{m.get('alert_id')})")
        else:
            a("_No correlated cases found._")
        a("")
        a("## 7. MITRE ATT&CK Mapping")
        for m in inv.get("mitre_mapping") or []:
            a(f"- **{m.get('technique_id','')} {m.get('technique','')}** ({m.get('tactic','')}) — {m.get('reason','')}")
        if not inv.get("mitre_mapping"):
            a("_No mapping available._")
        a("")
        a("## 8. Timeline")
        for t in inv.get("timeline") or []:
            a(f"- {t.get('timestamp','')} — {t.get('event','')} ({t.get('source','')})")
        if not inv.get("timeline"):
            a("_Timeline not reconstructed from available evidence._")
        a("")
        a("## 9. Verdict")
        a(f"**{inv.get('verdict', 'Needs Review')}**")
        a("")
        a("## 10. Confidence Score")
        a(f"**{inv.get('confidence_score', 0)}%** — {inv.get('reasoning_summary', '')}")
        if inv.get("false_positive_reasoning"):
            a("")
            a(f"**False-positive assessment:** {inv['false_positive_reasoning']}")
        a("")
        a("## 11. Evidence")
        for e in inv.get("evidence") or []:
            a(f"- [{e.get('importance','')}] {e.get('type','')}: {e.get('value','')} (source: {e.get('source','')})")
        if not inv.get("evidence"):
            a("_No discrete evidence items recorded._")
        a("")
        a("## 12. Missing Evidence")
        for m in inv.get("missing_evidence") or []:
            a(f"- {m}")
        a("")
        a("## 13. Recommended Actions")
        a("> All response actions are recommendations only and require human approval.")
        for act in inv.get("recommended_actions") or []:
            approval = "✋ human approval required" if act.get("requires_human_approval", True) else "auto-safe (read-only)"
            a(f"- **[{act.get('priority','medium')}]** {act.get('action','')} — _{approval}_. {act.get('reason','')}")
        a("")
        a("## 14. Customer Email Draft")
        a("```")
        a(inv.get("customer_email_draft", "") or "")
        a("```")
        a("")
        a("## 15. Ticket Update")
        a("```")
        a(inv.get("ticket_update", "") or "")
        a("```")
        a("")
        a("## 16. Detection Query Suggestions")
        for engine, label in [("splunk", "Splunk SPL"), ("crowdstrike_logscale", "CrowdStrike LogScale"),
                             ("wazuh", "Wazuh"), ("elastic_kql", "Elastic KQL"),
                             ("sigma", "Sigma"), ("sentinel_kql", "Microsoft Sentinel KQL")]:
            q = (inv.get("detection_query_suggestions") or {}).get(engine, "")
            if q:
                a(f"**{label}**")
                a("```")
                a(q)
                a("```")
        a("")
        a("## 17. Analyst Feedback")
        a("_Use the Feedback tab to record TP / FP / Benign / Duplicate / Escalated / Customer Confirmed._")
        if inv.get("qa_warnings"):
            a("")
            a("### QA Warnings")
            for w in inv["qa_warnings"]:
                a(f"- ⚠️ {w}")
        a("")
        a("---")
        a("_Generated by AutoSOC Command Center. Defensive analysis only — no automated containment performed._")
        return "\n".join(lines)
