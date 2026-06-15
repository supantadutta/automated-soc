"""Detection Engineer Agent — produces detection query suggestions across
Splunk, CrowdStrike LogScale, Wazuh, Elastic KQL, Sigma and Sentinel KQL.

Deterministic templates guarantee useful output offline; AI output (from the
Investigation Agent) overrides these when richer."""
from __future__ import annotations

from typing import Any


class DetectionEngineerAgent:
    name = "detection_engineer_agent"

    def suggest(self, normalized: dict[str, Any], category: str | None) -> dict[str, str]:
        src = normalized.get("src_ip") or "<src_ip>"
        user = normalized.get("username") or "<user>"
        host = normalized.get("hostname") or "<host>"
        domain = normalized.get("domain") or "<domain>"
        cat = (category or "generic").lower()

        if cat in {"dns", "dns_tunneling", "c2"}:
            return {
                "splunk": f'index=dns query="{domain}" | stats count by src_ip, query | sort -count',
                "crowdstrike_logscale": f'#event_simpleName=DnsRequest DomainName="{domain}" | groupBy([ComputerName, DomainName], function=count())',
                "wazuh": "rule idea: alert on DNS queries to low-reputation/long-entropy domains; fields: dns.question.name",
                "elastic_kql": f'dns.question.name:"{domain}" and event.category:"network"',
                "sigma": _sigma("Suspicious DNS Query", "dns", f"dns.question.name|contains: '{domain}'"),
                "sentinel_kql": f'DnsEvents | where Name == "{domain}" | summarize count() by ClientIP, Name',
            }
        if cat in {"sql_injection", "xss", "directory_traversal", "waf_attack"}:
            return {
                "splunk": 'index=web (uri_query="*\' OR*" OR uri_query="*../*" OR uri_query="*<script*") | stats count by src_ip, uri_path',
                "crowdstrike_logscale": f'#event_simpleName=HttpRequest RemoteIP="{src}" | groupBy([RemoteIP, UrlPath], function=count())',
                "wazuh": "rule idea: web attack signatures in URI/body; decoder: web-accesslog; fields: url, srcip",
                "elastic_kql": f'source.ip:"{src}" and url.query:(*OR* or *../* or *script*)',
                "sigma": _sigma("Web Application Attack Pattern", "webserver", "url.query|contains:\n      - \"' OR\"\n      - \"../\"\n      - \"<script\""),
                "sentinel_kql": 'W3CIISLog | where csUriQuery has_any ("\' OR", "../", "<script") | summarize count() by cIP, csUriStem',
            }
        # default: authentication anomaly
        return {
            "splunk": f'index=security sourcetype=auth src_ip={src} | stats count, dc(user) as users by src_ip | where users > 5',
            "crowdstrike_logscale": f'#event_simpleName=UserLogonFailed RemoteIP="{src}" | groupBy([RemoteIP, UserName], function=count()) | sort(_count, order=desc)',
            "wazuh": "rule idea: >5 failed auths from one src_ip in 5m; decoder: windows_eventchannel; fields: srcip, win.eventdata.targetUserName",
            "elastic_kql": f'event.category:"authentication" and source.ip:"{src}" and event.outcome:"failure"',
            "sigma": _sigma("Multiple Failed Authentications From Single Source", "authentication", "event.outcome: failure\n  condition: selection | count() by source.ip > 5"),
            "sentinel_kql": f'SigninLogs | where IPAddress == "{src}" | summarize attempts=count(), users=dcount(UserPrincipalName) by IPAddress | where users > 5',
        }


def _sigma(title: str, category: str, detection_body: str) -> str:
    return (
        f"title: {title}\n"
        "status: experimental\n"
        "logsource:\n"
        f"  category: {category}\n"
        "detection:\n"
        f"  selection:\n    {detection_body}\n"
        "  condition: selection\n"
        "falsepositives:\n  - Vulnerability scanners\n  - Authorized testing\n"
        "level: medium"
    )
