"""Parser/extraction tests."""
from __future__ import annotations

from app.parsers import collect_iocs, detect_category, extract_entities
from app.parsers.tool_parsers import crowdstrike_parser, wazuh_parser


def test_extracts_source_and_dest_ip():
    text = "Connection from 203.0.113.10 to 10.20.5.7 observed."
    ents = extract_entities(text)
    assert ents["src_ip"] == "203.0.113.10"
    assert ents["dest_ip"] == "10.20.5.7"


def test_extracts_hash_and_domain():
    text = "sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 to evil-c2.example"
    ents = extract_entities(text)
    assert ents["file_hash"].startswith("e3b0c4")
    assert "evil-c2.example" in ents["all_domains"]


def test_detect_category_password_spray():
    assert detect_category("Password spray detected against M365", "Password Spray") == "password_spray"


def test_detect_category_sql_injection():
    assert detect_category("WAF blocked union select id from users") == "sql_injection"


def test_crowdstrike_parser_maps_username():
    raw_json = {"DetectName": "Suspicious AD", "UserName": "svc-backup",
                "ComputerName": "DC01", "RemoteIP": "192.168.143.84"}
    fields = crowdstrike_parser("", raw_json)
    assert fields["username"] == "svc-backup"
    assert fields["hostname"] == "DC01"
    assert fields["source_tool"] == "CrowdStrike"


def test_wazuh_parser_reads_nested_fields():
    raw_json = {"rule": {"description": "SSH Brute Force", "level": 10},
                "data": {"srcip": "198.51.100.91", "dstuser": "root"}}
    fields = wazuh_parser("", raw_json)
    assert fields["src_ip"] == "198.51.100.91"
    assert fields["alert_name"] == "SSH Brute Force"


def test_collect_iocs_dedup():
    norm = {"all_ips": ["203.0.113.10", "203.0.113.10"], "all_hashes": [], "all_domains": ["evil-c2.example"],
            "all_urls": [], "username": "jdoe"}
    iocs = collect_iocs(norm)
    values = [i["value"] for i in iocs]
    assert values.count("203.0.113.10") == 1
    assert {"ioc_type": "username", "value": "jdoe"} in iocs
