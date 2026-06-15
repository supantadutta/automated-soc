"""Per-tool field mappers.

Each parser takes a raw payload (dict if JSON, else text) and returns a partial
normalized-field dict. Unknown formats fall back to the generic parser.
"""
from __future__ import annotations

from typing import Any

from app.parsers.extract import detect_category, extract_entities


def _first(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d.get(k)
    return default


def generic_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    ents = extract_entities(raw_text)
    fields: dict[str, Any] = dict(ents)
    if raw_json:
        fields["username"] = _first(raw_json, "user", "username", "user_name", "UserName", "account")
        fields["hostname"] = _first(raw_json, "host", "hostname", "ComputerName", "computer", "device")
        fields["src_ip"] = _first(raw_json, "src_ip", "source_ip", "RemoteIP", "client_ip") or ents.get("src_ip")
        fields["dest_ip"] = _first(raw_json, "dest_ip", "destination_ip", "LocalIP") or ents.get("dest_ip")
        fields["alert_name"] = _first(raw_json, "alert_name", "title", "name", "rule_name", "DetectName")
        fields["severity"] = _first(raw_json, "severity", "Severity", "priority")
        fields["event_time"] = _first(raw_json, "timestamp", "time", "event_time", "@timestamp", "EventTime")
        fields["source_tool"] = _first(raw_json, "source_tool", "tool", "vendor", "product")
        fields["process_name"] = _first(raw_json, "process", "process_name", "ImageFileName")
        fields["command_line"] = _first(raw_json, "command_line", "CommandLine", "cmdline")
        fields["domain"] = _first(raw_json, "domain", "DomainName", "query") or ents.get("domain")
        fields["file_hash"] = _first(raw_json, "sha256", "hash", "SHA256HashData", "md5") or ents.get("file_hash")
    return fields


def crowdstrike_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        f["alert_name"] = _first(raw_json, "DetectName", "alert_name", "name") or f.get("alert_name")
        f["username"] = _first(raw_json, "UserName", "user") or f.get("username")
        f["hostname"] = _first(raw_json, "ComputerName", "host") or f.get("hostname")
        f["process_name"] = _first(raw_json, "FileName", "ImageFileName") or f.get("process_name")
        f["command_line"] = _first(raw_json, "CommandLine") or f.get("command_line")
    f["source_tool"] = f.get("source_tool") or "CrowdStrike"
    return f


def splunk_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        f["username"] = _first(raw_json, "user", "User") or f.get("username")
        f["src_ip"] = _first(raw_json, "src", "src_ip") or f.get("src_ip")
        f["dest_ip"] = _first(raw_json, "dest", "dest_ip") or f.get("dest_ip")
        f["alert_name"] = _first(raw_json, "search_name", "savedsearch_name") or f.get("alert_name")
    f["source_tool"] = f.get("source_tool") or "Splunk"
    return f


def wazuh_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        rule = raw_json.get("rule", {}) if isinstance(raw_json.get("rule"), dict) else {}
        data = raw_json.get("data", {}) if isinstance(raw_json.get("data"), dict) else {}
        f["alert_name"] = rule.get("description") or f.get("alert_name")
        f["severity"] = str(rule.get("level")) if rule.get("level") is not None else f.get("severity")
        f["src_ip"] = data.get("srcip") or f.get("src_ip")
        f["username"] = data.get("dstuser") or data.get("srcuser") or f.get("username")
    f["source_tool"] = f.get("source_tool") or "Wazuh"
    return f


def elastic_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        src = raw_json.get("source", {}) if isinstance(raw_json.get("source"), dict) else {}
        user = raw_json.get("user", {}) if isinstance(raw_json.get("user"), dict) else {}
        host = raw_json.get("host", {}) if isinstance(raw_json.get("host"), dict) else {}
        f["src_ip"] = src.get("ip") or f.get("src_ip")
        f["username"] = user.get("name") or f.get("username")
        f["hostname"] = host.get("name") or f.get("hostname")
    f["source_tool"] = f.get("source_tool") or "Elastic"
    return f


def suricata_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        alert = raw_json.get("alert", {}) if isinstance(raw_json.get("alert"), dict) else {}
        f["alert_name"] = alert.get("signature") or f.get("alert_name")
        f["severity"] = str(alert.get("severity")) if alert.get("severity") is not None else f.get("severity")
        f["src_ip"] = raw_json.get("src_ip") or f.get("src_ip")
        f["dest_ip"] = raw_json.get("dest_ip") or f.get("dest_ip")
    f["source_tool"] = f.get("source_tool") or "Suricata"
    return f


def waf_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    f = generic_parser(raw_text, raw_json)
    f["source_tool"] = f.get("source_tool") or "WAF/F5"
    return f


def sentinel_parser(raw_text: str, raw_json: dict | None) -> dict[str, Any]:
    # Placeholder mapping for Microsoft Sentinel incidents.
    f = generic_parser(raw_text, raw_json)
    if raw_json:
        props = raw_json.get("properties", {}) if isinstance(raw_json.get("properties"), dict) else {}
        f["alert_name"] = props.get("title") or f.get("alert_name")
        f["severity"] = props.get("severity") or f.get("severity")
    f["source_tool"] = f.get("source_tool") or "Microsoft Sentinel"
    return f


PARSERS = {
    "crowdstrike": crowdstrike_parser,
    "splunk": splunk_parser,
    "wazuh": wazuh_parser,
    "elastic": elastic_parser,
    "suricata": suricata_parser,
    "waf": waf_parser,
    "f5": waf_parser,
    "sentinel": sentinel_parser,
    "generic": generic_parser,
}


def select_parser(source_tool: str | None):
    if not source_tool:
        return generic_parser
    key = source_tool.lower()
    for name, fn in PARSERS.items():
        if name in key:
            return fn
    return generic_parser
