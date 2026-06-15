"""Regex-based entity extraction and alert category detection.

These run fully offline and form the deterministic backbone of normalization.
"""
from __future__ import annotations

import re
from typing import Any

IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")
MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA1 = re.compile(r"\b[a-fA-F0-9]{40}\b")
SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")
DOMAIN = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")
URL = re.compile(r"https?://[^\s\"'<>]+")
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

PRIVATE_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "127.")

# Keyword -> normalized category
CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("password_spray", ["password spray", "spray"]),
    ("brute_force", ["brute force", "brute-force", "multiple failed", "failed login", "failed authentication"]),
    ("ssh_brute_force", ["ssh", "sshd"]),
    ("rdp_anomaly", ["rdp", "remote desktop", "3389"]),
    ("credential_dumping", ["lsass", "credential dump", "mimikatz", "sekurlsa"]),
    ("dll_injection", ["dll injection", "process injection", "reflective"]),
    ("powershell", ["powershell", "encodedcommand", "-enc ", "invoke-expression", "iex"]),
    ("malware", ["malware", "trojan", "ransomware", "malicious file", "virus", "quarantine"]),
    ("directory_traversal", ["../", "..%2f", "directory traversal", "path traversal"]),
    ("sql_injection", ["sql injection", "sqli", "union select", "' or '1'='1"]),
    ("xss", ["xss", "<script", "cross-site scripting", "onerror="]),
    ("waf_attack", ["waf", "f5", "asm", "web application firewall blocked"]),
    ("dns_tunneling", ["dns tunnel", "dns tunneling", "high entropy dns"]),
    ("dns", ["dns query", "suspicious dns", "nxdomain"]),
    ("c2", ["command and control", "c2", "beacon", "callback"]),
    ("lateral_movement", ["lateral movement", "smb", "psexec", "admin$", "wmiexec"]),
    ("suspicious_auth", ["active directory authentication", "kerberos", "ad authentication"]),
    ("new_endpoint", ["new endpoint", "new device", "first seen host"]),
    ("unusual_login", ["unusual login", "impossible travel", "anomalous login", "new geo"]),
]


def _public_ips(text: str) -> list[str]:
    ips = IPV4.findall(text)
    return [ip for ip in ips if not ip.startswith(PRIVATE_PREFIXES)]


def extract_entities(text: str) -> dict[str, Any]:
    """Extract indicators from free text. Returns normalized field dict."""
    text = text or ""
    all_ips = IPV4.findall(text)
    hashes = SHA256.findall(text) or SHA1.findall(text) or MD5.findall(text)
    urls = URL.findall(text)
    # Domains excluding ones that are just IPs or file extensions noise
    domains = [
        d for d in DOMAIN.findall(text)
        if not IPV4.match(d) and not d.lower().endswith((".exe", ".dll", ".ps1", ".bat", ".sh"))
    ]
    emails = EMAIL.findall(text)

    result: dict[str, Any] = {
        "src_ip": all_ips[0] if all_ips else None,
        "dest_ip": all_ips[1] if len(all_ips) > 1 else None,
        "file_hash": hashes[0] if hashes else None,
        "url": urls[0] if urls else None,
        "domain": domains[0] if domains else None,
        "all_ips": all_ips,
        "all_hashes": hashes,
        "all_domains": list(dict.fromkeys(domains)),
        "all_urls": urls,
        "all_emails": emails,
    }
    return result


def detect_category(text: str, alert_name: str | None = None) -> str:
    haystack = f"{alert_name or ''} {text or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in haystack for k in keywords):
            return category
    return "generic"


def collect_iocs(normalized: dict[str, Any]) -> list[dict[str, str]]:
    """Build a de-duplicated IOC list from normalized fields."""
    iocs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(ioc_type: str, value: str | None):
        if not value:
            return
        key = (ioc_type, str(value))
        if key in seen:
            return
        seen.add(key)
        iocs.append({"ioc_type": ioc_type, "value": str(value)})

    for ip in normalized.get("all_ips", []) or []:
        if not ip.startswith(PRIVATE_PREFIXES):
            add("ip", ip)
    for h in normalized.get("all_hashes", []) or []:
        add("hash", h)
    for d in normalized.get("all_domains", []) or []:
        add("domain", d)
    for u in normalized.get("all_urls", []) or []:
        add("url", u)
    if normalized.get("username"):
        add("username", normalized["username"])
    if normalized.get("hostname"):
        add("hostname", normalized["hostname"])
    return iocs
