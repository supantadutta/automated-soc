"""End-to-end API tests using the mock AI provider."""
from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_login_me(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "Password1!",
                                        "organization_name": "Acme"})
    login = client.post("/auth/login", json={"email": "a@b.com", "password": "Password1!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.com"


def test_create_and_investigate_alert(client, auth_headers):
    raw = ('{"alert_name":"C2 Beacon","source_tool":"Suricata","severity":"Critical",'
           '"src_ip":"10.20.8.55","domain":"beacon.evil-c2.example",'
           '"detail":"Periodic beaconing to known command-and-control domain"}')
    create = client.post("/alerts", json={"raw_payload": raw, "source_tool": "Suricata",
                                          "severity": "Critical"}, headers=auth_headers)
    assert create.status_code == 201
    alert_id = create.json()["id"]

    # Parse
    parsed = client.post(f"/alerts/{alert_id}/parse", headers=auth_headers)
    assert parsed.status_code == 200
    assert parsed.json()["category"] == "c2"

    # Investigate (auto-runs enrich)
    inv = client.post(f"/alerts/{alert_id}/investigate", json={"provider": "mock"},
                      headers=auth_headers)
    assert inv.status_code == 200
    body = inv.json()
    assert body["verdict"] in {
        "True Positive", "Needs Review", "Benign Authorized Activity",
        "False Positive", "Duplicate", "Escalated",
    }
    assert "result" in body

    # Generate report
    report = client.post(f"/alerts/{alert_id}/generate-report", headers=auth_headers)
    assert report.status_code == 200
    rid = report.json()["id"]
    md = client.get(f"/reports/{rid}/markdown", headers=auth_headers)
    assert md.status_code == 200
    assert "SOC Investigation Report" in md.text


def test_malicious_ioc_drives_true_positive(client, auth_headers):
    raw = ('{"alert_name":"C2","source_tool":"Suricata","severity":"Critical",'
           '"src_ip":"10.20.8.55","dest_ip":"203.0.113.66","domain":"beacon.evil-c2.example"}')
    create = client.post("/alerts", json={"raw_payload": raw}, headers=auth_headers)
    alert_id = create.json()["id"]
    inv = client.post(f"/alerts/{alert_id}/investigate", json={"provider": "mock"}, headers=auth_headers)
    assert inv.json()["verdict"] == "True Positive"


def test_ai_providers_listed(client, auth_headers):
    resp = client.get("/ai/providers", headers=auth_headers)
    assert resp.status_code == 200
    keys = {p["provider"] for p in resp.json()["providers"]}
    assert {"openai", "anthropic", "ollama", "mock", "vllm", "lmstudio"}.issubset(keys)


def test_dashboard_summary(client, auth_headers):
    resp = client.get("/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert "severity_breakdown" in resp.json()
