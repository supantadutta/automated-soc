"""API tests for the upgraded AI endpoints."""
from __future__ import annotations


def test_capabilities_endpoint(client, auth_headers):
    r = client.get("/ai/capabilities", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert any(m["provider"] == "ollama" for m in body["models"])
    assert "local_only" in body["routing_policies"]


def test_models_grouped(client, auth_headers):
    r = client.get("/ai/models", headers=auth_headers)
    assert r.status_code == 200
    assert "openai" in r.json()["by_provider"]


def test_runtime_config_get_and_update(client, auth_headers):
    r = client.get("/ai/config", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["source"] == "env"

    upd = client.put("/ai/config", json={"default_provider": "ollama", "routing_mode": "local_only"},
                     headers=auth_headers)
    assert upd.status_code == 200
    assert upd.json()["default_provider"] == "ollama"
    assert upd.json()["routing_mode"] == "privacy"
    assert upd.json()["source"] == "runtime"

    # Change is audited
    audit = client.get("/audit-logs?action=ai.config.update", headers=auth_headers)
    assert any(l["action"] == "ai.config.update" for l in audit.json())


def test_prompt_versioning(client, auth_headers):
    listed = client.get("/ai/prompts", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 5

    created = client.post("/ai/prompts", json={
        "prompt_type": "soc_investigation",
        "template": "Custom evidence-based JSON prompt with confidence and human approval.",
        "name": "custom v2",
    }, headers=auth_headers)
    assert created.status_code == 200
    pid = created.json()["id"]
    assert created.json()["version"] >= 2
    assert created.json()["is_active"] is True

    ev = client.post(f"/ai/prompts/{pid}/test", headers=auth_headers)
    assert ev.status_code == 200
    assert 0 <= ev.json()["score"] <= 100


def test_providers_list_includes_privacy_metadata(client, auth_headers):
    r = client.get("/ai/providers", headers=auth_headers)
    providers = r.json()["providers"]
    ollama = next(p for p in providers if p["provider"] == "ollama")
    assert ollama["privacy_level"] == "local"
    openai = next(p for p in providers if p["provider"] == "openai")
    assert openai["privacy_level"] == "external"
    # No secrets ever leak to the frontend
    assert "api_key" not in str(r.json()).lower() or "***" not in str(r.json())


def test_ai_operations_has_timeseries(client, auth_headers):
    # Investigate to generate at least one ai_run
    raw = '{"alert_name":"C2","source_tool":"Suricata","domain":"beacon.evil-c2.example","src_ip":"10.20.8.55"}'
    a = client.post("/alerts", json={"raw_payload": raw}, headers=auth_headers).json()
    client.post(f"/alerts/{a['id']}/investigate", json={"provider": "mock"}, headers=auth_headers)
    ops = client.get("/dashboard/ai-operations", headers=auth_headers)
    assert ops.status_code == 200
    body = ops.json()
    assert "timeseries" in body and "top_expensive_investigations" in body
    assert "failed_calls" in body and "fallback_events" in body
