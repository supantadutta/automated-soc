# SOC Investigation Report — SSH Brute Force Followed by Successful Authentication

## Executive Summary

AutoSOC's detection pipeline raised a high-severity alert for repeated failed SSH authentication attempts against the customer's internet-facing bastion host `bastion-prod-01` (10.20.5.11), originating from a single external source address `203.0.113.45`. Over a ~9 minute window the source generated 248 failed `password` authentication attempts against the `svc_deploy` account, immediately followed by **one successful** authentication from the same address. This pattern — high-volume sequential failures terminating in a success against the same target account from the same source — is consistent with a successful credential brute-force ending in account takeover.

Based on the volume, the single-source/single-account focus, and the success event correlating tightly with the failure burst, the analyst assessment is **Likely True Positive** with a confidence of **82%**. This is not yet confirmed compromise: we lack post-authentication session telemetry (commands executed, lateral movement, data access) that would elevate this to a confirmed intrusion. Recommended containment actions below require analyst approval before execution.

## Alert Overview

| Field | Value |
|---|---|
| Alert ID | ALRT-2026-0614-009823 |
| Source Tool | Linux auditd -> SIEM (correlation rule `SSH-BRUTE-SUCCESS`) |
| Severity | High |
| Detected At | 2026-06-14 02:47:13 UTC |
| Customer | Northwind Logistics (CUST-0142) |
| Status | Under Investigation |

## Technical Analysis

The detection correlation rule fired on a threshold breach: >= 50 failed SSH `Failed password` events for a single `(source_ip, target_user)` tuple within a 10-minute sliding window, followed by an `Accepted password` event for the same tuple inside the same window.

Log review of `/var/log/auth.log` (forwarded to the SIEM) confirms:

- **248** `Failed password for svc_deploy from 203.0.113.45 port <varies> ssh2` entries between 02:38:41 and 02:47:09 UTC. Source ports increment sequentially and connection rate averages ~28 attempts/minute — consistent with an automated tool rather than human typing.
- A single `Accepted password for svc_deploy from 203.0.113.45 port 51884 ssh2` at **02:47:11 UTC**, two seconds before the alert fired.
- The session opened a PTY: `pam_unix(sshd:session): session opened for user svc_deploy by (uid=0)`.

The `svc_deploy` account is a service account used by the CI/CD pipeline. Per the customer's documented baseline, this account normally authenticates **only via SSH key** from the internal build runner (10.20.9.30) — password authentication for this account is unexpected and, per the runbook, should be disabled. The presence of a successful *password* authentication from an external address is therefore anomalous on two axes: the authentication method and the source network.

No follow-on process-execution or network telemetry from the host has yet been ingested for the post-login window, so the actions taken during the authenticated session are currently unknown. This is the primary gap preventing a "True Positive / Confirmed Compromise" verdict.

## Affected Entities

**Hosts**
- `bastion-prod-01` (10.20.5.11) — target host, internet-facing on TCP/22.

**Users**
- `svc_deploy` — CI/CD service account; target of the brute force and the account that successfully authenticated.

**IPs**
- `203.0.113.45` — external source of all failed attempts and the successful login (documentation IP used here as a safe stand-in).
- `10.20.9.30` — legitimate internal build runner (expected source for this account; **not** involved in this event — listed for contrast).

## IOC Enrichment

| Indicator | Type | Reputation Source | Verdict |
|---|---|---|---|
| 203.0.113.45 | IPv4 | Internal threat-intel feed | No prior record |
| 203.0.113.45 | IPv4 | Passive DNS (internal) | No PTR; no associated domains |
| 203.0.113.45 | IPv4 | GeoIP enrichment | Resolves to hosting/ASN range (non-residential) |
| svc_deploy | Account | IAM directory | Valid active service account |

> Note: Reputation sources returned no prior malicious history for `203.0.113.45`. The absence of a bad reputation does **not** exonerate the source — the behavioral evidence (volume + success) is the load-bearing signal here, not reputation.

## Case Correlation

- **ALRT-2026-0614-009811** (Medium, 02:39 UTC): "Multiple authentication failures — single host" on the same `bastion-prod-01`. This is the lower-severity precursor that the brute-force rule later superseded. Correlated into this case.
- No other open cases reference `203.0.113.45` or `svc_deploy` in the trailing 30 days.
- Threat-hunt query for the same source against other customer-tenant bastions returned no hits — activity appears scoped to this single tenant/host.

## MITRE ATT&CK Mapping

| Tactic | Technique ID | Technique Name | Evidence |
|---|---|---|---|
| Credential Access | T1110.001 | Brute Force: Password Guessing | 248 sequential failed password attempts from a single source against one account |
| Credential Access | T1110.003 | Brute Force: Password Spraying | Considered but not supported — activity targets a single account, not many; included as a ruled-out alternative |
| Initial Access | T1078 | Valid Accounts | Successful password authentication as `svc_deploy` from external source |
| Lateral Movement | T1021.004 | Remote Services: SSH | Interactive SSH session established post-authentication |

## Timeline

| Time (UTC) | Event |
|---|---|
| 2026-06-14 02:38:41 | First `Failed password for svc_deploy from 203.0.113.45` |
| 2026-06-14 02:39:10 | Precursor alert ALRT-...009811 raised (auth failures) |
| 2026-06-14 02:38:41 - 02:47:09 | 248 failed attempts (~28/min) |
| 2026-06-14 02:47:11 | `Accepted password for svc_deploy from 203.0.113.45` — session opened |
| 2026-06-14 02:47:13 | Correlation rule `SSH-BRUTE-SUCCESS` fires -> ALRT-...009823 |
| 2026-06-14 02:51:00 | AutoSOC enrichment + auto-triage complete; routed to analyst queue |

## Verdict

**Likely True Positive.**

The evidence strongly supports a successful brute-force authentication: a tight burst of failed attempts at machine speed, single-source and single-account focus, terminating in a successful password login using an authentication method and source that are both outside the documented baseline for this account. The reason the verdict is "Likely" rather than confirmed "True Positive (Compromise)" is the absence of post-authentication activity telemetry — we can evidence the *unauthorized access* but cannot yet evidence *what was done* with it.

## Confidence Score

**82%.**

Rationale: High weight on the behavioral pattern (volume, rate, single-tuple focus, success timing) and the baseline deviation (password auth for a key-only account from an external IP). Confidence is held below 90% because: (a) we have not yet confirmed the session's post-login actions, and (b) there is a low-probability benign explanation (a misconfigured automation re-trying a stale password and eventually matching) that cannot be fully excluded without runner/CI logs. The deduction keeps us honest rather than overstating compromise.

## Evidence

- 248 `Failed password` events for `svc_deploy` from `203.0.113.45` within ~9 minutes at a consistent automated rate.
- A single `Accepted password` for the same account from the same source immediately after the failure burst.
- `svc_deploy` baseline is key-only auth from internal runner `10.20.9.30`; observed event is password auth from an external host — a clear deviation.
- GeoIP places the source in a hosting/ASN range, not a residential or known-corporate range.

## Missing Evidence

- Post-authentication shell history / `auditd` `execve` records for the `svc_deploy` session.
- Outbound network connections from `bastion-prod-01` during/after 02:47 UTC (possible lateral movement or staging).
- Whether SSH password authentication was actually enabled on this host (`sshd_config`), confirming the success was possible as observed.
- CI/CD runner logs to rule out a benign automation misfire as the source of the success.
- Source-IP attribution data (is `203.0.113.45` a known customer egress, VPN, or third-party?).

## Recommended Actions

1. **[Recommendation - requires analyst approval]** Disable / lock the `svc_deploy` account pending review, and rotate its credentials and any associated SSH keys.
2. **[Recommendation - requires analyst approval]** Block `203.0.113.45` at the perimeter firewall for inbound TCP/22 to the bastion segment.
3. **[Recommendation - requires analyst approval]** Isolate or snapshot `bastion-prod-01` for forensic capture before remediation (preserve memory and `auth.log`/auditd).
4. **[Recommendation - requires analyst approval]** Collect and review post-login `auditd` `execve` and network telemetry for the 02:47 UTC session.
5. **[Recommendation - requires analyst approval]** Confirm `sshd_config` enforces `PasswordAuthentication no` / key-only auth for service accounts; remediate if not.
6. **[Recommendation - requires analyst approval]** Hunt for `203.0.113.45` and `svc_deploy` usage across the rest of the customer estate over the past 30 days.

## Customer Email Draft

> **Subject:** AutoSOC Investigation — SSH authentication activity on bastion-prod-01 (CUST-0142)
>
> Hello Northwind Logistics team,
>
> Our monitoring detected a series of failed SSH login attempts against your bastion host `bastion-prod-01`, targeting the `svc_deploy` service account from a single external address, followed by one successful login using that account. Because this account is normally expected to authenticate only via key from your internal build runner, we are treating this as a likely unauthorized access and have flagged it for your attention.
>
> At this stage we have confirmed the access event but have not yet determined what actions, if any, were taken during the session. As a precaution we recommend rotating the `svc_deploy` credentials/keys and temporarily blocking the source address. We have prepared the specific containment steps and will execute them on your approval — no changes have been made to your environment.
>
> We will follow up as our review of the post-login activity completes. Please reach out with any questions.
>
> Regards,
> AutoSOC Command Center — SOC Operations

## Ticket Update

Status: **Under Investigation -> Pending Customer Approval.** Confirmed brute-force pattern (248 fails) + 1 success against `svc_deploy` from `203.0.113.45`. Verdict: Likely True Positive (82%). Containment recommendations drafted and awaiting analyst/customer approval. Blocking gap: post-login session telemetry not yet ingested.

## Detection Query Suggestions

Illustrative only — adapt field names to your schema.

```kql
// KQL — failed-then-successful SSH from same source/account (Sentinel-style)
Syslog
| where Facility == "auth" and ProcessName == "sshd"
| extend SrcIP = extract(@"from (\d+\.\d+\.\d+\.\d+)", 1, SyslogMessage)
| extend TargetUser = extract(@"for (\w+)", 1, SyslogMessage)
| summarize Fails = countif(SyslogMessage has "Failed password"),
            Success = countif(SyslogMessage has "Accepted password")
  by SrcIP, TargetUser, bin(TimeGenerated, 10m)
| where Fails >= 50 and Success >= 1
```

```sql
-- SPL (Splunk-style)
index=linux sourcetype=linux_secure (Failed OR Accepted) password
| rex "from (?<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "for (?<user>\w+)"
| bin _time span=10m
| stats count(eval(searchmatch("Failed"))) as fails count(eval(searchmatch("Accepted"))) as success by src_ip user _time
| where fails>=50 AND success>=1
```

```yaml
# Sigma-style (illustrative)
title: SSH Brute Force Followed by Success
logsource: { product: linux, service: sshd }
detection:
  fails:   { message|contains: 'Failed password' }
  success: { message|contains: 'Accepted password' }
  timeframe: 10m
  condition: fails | count() by src_ip,user >= 50 and success
level: high
```

## Analyst Feedback Section

```
Verdict agree? (Y/N):  ____
Corrected verdict (if any):  ____________________________
Notes:  ________________________________________________
        ________________________________________________
Analyst:  ____________________     Date:  ______________
```
