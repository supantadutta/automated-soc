"""Security hardening: encryption, masking, JWT refresh/revocation, isolation,
payload cap, knowledge/approval workflow."""
from __future__ import annotations

from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret


# --- Crypto ----------------------------------------------------------------
def test_encrypt_roundtrip_and_not_plaintext():
    ct = encrypt_secret("sk-super-secret")
    assert ct and ct != "sk-super-secret"
    assert decrypt_secret(ct) == "sk-super-secret"


def test_mask_secret_keeps_only_suffix():
    assert mask_secret("sk-abcdefgh1234") == "****1234"
    assert mask_secret("xy") == "****"
    assert mask_secret("") == ""


# --- JWT refresh + revocation ---------------------------------------------
def test_refresh_and_logout_revokes_tokens(client):
    client.post("/auth/register", json={"email": "rev@x.com", "password": "Password1!",
                                        "organization_name": "RevOrg"})
    login = client.post("/auth/login", json={"email": "rev@x.com", "password": "Password1!"}).json()
    assert login["refresh_token"]
    access = {"Authorization": f"Bearer {login['access_token']}"}

    # refresh works
    refreshed = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refreshed.status_code == 200

    # logout bumps token_version → old access token now rejected
    assert client.post("/auth/logout", headers=access).status_code == 200
    assert client.get("/auth/me", headers=access).status_code == 401
    # and the old refresh token is revoked too
    assert client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401


# --- Tenant isolation ------------------------------------------------------
def test_two_org_isolation(client):
    # Org A
    client.post("/auth/register", json={"email": "a@orgA.com", "password": "Password1!",
                                        "organization_name": "OrgA"})
    a = client.post("/auth/login", json={"email": "a@orgA.com", "password": "Password1!"}).json()
    ha = {"Authorization": f"Bearer {a['access_token']}"}
    alert_a = client.post("/alerts", json={"raw_payload": "orgA secret alert 10.0.0.1"}, headers=ha).json()

    # Org B
    client.post("/auth/register", json={"email": "b@orgB.com", "password": "Password1!",
                                        "organization_name": "OrgB"})
    b = client.post("/auth/login", json={"email": "b@orgB.com", "password": "Password1!"}).json()
    hb = {"Authorization": f"Bearer {b['access_token']}"}

    # Org B cannot see Org A's alert, and its list is empty of it
    assert client.get(f"/alerts/{alert_a['id']}", headers=hb).status_code == 404
    b_alerts = client.get("/alerts", headers=hb).json()
    assert all(x["id"] != alert_a["id"] for x in b_alerts)


# --- Payload size cap ------------------------------------------------------
def test_oversized_payload_rejected(client, auth_headers):
    big = "A" * 200_001
    r = client.post("/alerts", json={"raw_payload": big}, headers=auth_headers)
    assert r.status_code == 413


# --- Knowledge docs + approval workflow ------------------------------------
def test_knowledge_doc_then_retrievable(client, auth_headers):
    doc = client.post("/knowledge", json={
        "title": "Test SOP", "content": "approved scanner 203.0.113.99 runs nightly",
    }, headers=auth_headers)
    assert doc.status_code == 201
    listed = client.get("/knowledge", headers=auth_headers).json()
    assert any(d["title"] == "Test SOP" for d in listed)


def test_approval_workflow(client, auth_headers):
    # Investigate to create recommendations
    raw = '{"alert_name":"C2","source_tool":"Suricata","domain":"beacon.evil-c2.example","src_ip":"10.20.8.55"}'
    a = client.post("/alerts", json={"raw_payload": raw}, headers=auth_headers).json()
    inv = client.post(f"/alerts/{a['id']}/investigate", json={"provider": "mock"}, headers=auth_headers).json()
    recs = client.get(f"/investigations/{inv['id']}/recommendations", headers=auth_headers).json()
    assert recs, "investigation should yield response recommendations"

    req = client.post(f"/recommendations/{recs[0]['id']}/request-approval", headers=auth_headers)
    assert req.status_code == 200
    approval_id = req.json()["id"]

    decided = client.post(f"/approvals/{approval_id}/decision", json={"decision": "approved"}, headers=auth_headers)
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
    # decision is audited
    audit = client.get("/audit-logs?action=approval.approved", headers=auth_headers).json()
    assert any(l["action"] == "approval.approved" for l in audit)
