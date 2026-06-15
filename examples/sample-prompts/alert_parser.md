# alert_parser

**System:** guardrails + "You parse a raw security alert and extract normalized fields as JSON."

**User:**
```
Parse this raw alert from source tool 'CrowdStrike'.
Extract these fields as a JSON object (use null when absent):
alert_name, source_tool, severity, event_time, src_ip, dest_ip, username,
hostname, domain, url, file_hash, process_name, command_line, category.

category must be one of: brute_force, password_spray, suspicious_auth,
unusual_login, new_endpoint, rdp_anomaly, ssh_brute_force, powershell, malware,
credential_dumping, dll_injection, directory_traversal, sql_injection, xss,
waf_attack, dns, dns_tunneling, c2, lateral_movement, generic.

=== RAW ALERT ===
{"DetectName":"Suspicious AD Authentication","UserName":"svc-backup","ComputerName":"DC01","RemoteIP":"192.168.143.84"}
```

**Expected JSON:**
```json
{ "alert_name": "Suspicious AD Authentication", "source_tool": "CrowdStrike",
  "username": "svc-backup", "hostname": "DC01", "src_ip": "192.168.143.84",
  "category": "suspicious_auth", "severity": null }
```
