"""Threat Intel / MITRE ATT&CK Agent.

Provides a deterministic category->technique baseline so mapping works offline;
the Investigation Agent's AI output can refine/extend this.
"""
from __future__ import annotations

from typing import Any

CATEGORY_MITRE: dict[str, list[dict[str, Any]]] = {
    "brute_force": [{"tactic": "Credential Access", "technique": "Brute Force", "technique_id": "T1110"}],
    "password_spray": [{"tactic": "Credential Access", "technique": "Password Spraying", "technique_id": "T1110.003"}],
    "suspicious_auth": [{"tactic": "Credential Access", "technique": "Brute Force", "technique_id": "T1110"}],
    "ssh_brute_force": [{"tactic": "Credential Access", "technique": "Brute Force: SSH", "technique_id": "T1110.001"}],
    "rdp_anomaly": [{"tactic": "Lateral Movement", "technique": "Remote Services: RDP", "technique_id": "T1021.001"}],
    "powershell": [{"tactic": "Execution", "technique": "PowerShell", "technique_id": "T1059.001"}],
    "credential_dumping": [{"tactic": "Credential Access", "technique": "OS Credential Dumping", "technique_id": "T1003"}],
    "dll_injection": [{"tactic": "Defense Evasion", "technique": "Process Injection", "technique_id": "T1055"}],
    "malware": [{"tactic": "Execution", "technique": "User Execution", "technique_id": "T1204"}],
    "directory_traversal": [{"tactic": "Initial Access", "technique": "Exploit Public-Facing Application", "technique_id": "T1190"}],
    "sql_injection": [{"tactic": "Initial Access", "technique": "Exploit Public-Facing Application", "technique_id": "T1190"}],
    "xss": [{"tactic": "Initial Access", "technique": "Exploit Public-Facing Application", "technique_id": "T1190"}],
    "waf_attack": [{"tactic": "Initial Access", "technique": "Exploit Public-Facing Application", "technique_id": "T1190"}],
    "dns": [{"tactic": "Command and Control", "technique": "Application Layer Protocol: DNS", "technique_id": "T1071.004"}],
    "dns_tunneling": [{"tactic": "Exfiltration", "technique": "Exfiltration Over C2 Channel", "technique_id": "T1041"}],
    "c2": [{"tactic": "Command and Control", "technique": "Application Layer Protocol", "technique_id": "T1071"}],
    "lateral_movement": [{"tactic": "Lateral Movement", "technique": "Remote Services: SMB", "technique_id": "T1021.002"}],
    "unusual_login": [{"tactic": "Initial Access", "technique": "Valid Accounts", "technique_id": "T1078"}],
    "new_endpoint": [{"tactic": "Initial Access", "technique": "Valid Accounts", "technique_id": "T1078"}],
}


class MitreAgent:
    name = "mitre_agent"

    def baseline(self, category: str | None) -> list[dict[str, Any]]:
        items = CATEGORY_MITRE.get((category or "").lower(), [])
        out = []
        for it in items:
            out.append({**it, "confidence": 60, "reason": f"Baseline mapping for category '{category}'."})
        return out
