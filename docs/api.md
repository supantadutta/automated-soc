# API Reference

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger) and `/redoc`.

All endpoints except `/health`, `/auth/login`, and `/auth/register` require a Bearer JWT:

```
Authorization: Bearer <access_token>
```

Roles: `platform_admin`, `organization_admin`, `soc_manager`, `analyst`, `viewer`. Write endpoints require analyst or above; `viewer` is read-only.

---

## System

### `GET /health`
```json
{ "status": "ok", "app": "AutoSOC Command Center", "default_provider": "mock", "routing_mode": "auto" }
```

---

## Auth

### `POST /auth/register`
Request: `{ "email": "you@org.com", "password": "Password1!", "full_name": "Jane", "organization_name": "Acme MSSP" }`
Response: `{ "access_token": "...", "token_type": "bearer", "role": "organization_admin", "email": "you@org.com" }`

### `POST /auth/login`
Request: `{ "email": "admin@autosoc.local", "password": "Admin123!" }`
Response: same shape as register.

### `GET /auth/me`
Response: `{ "id": 1, "email": "...", "role": "platform_admin", "organization_id": 1 }`

---

## Customers

| Method | Path | Description |
|---|---|---|
| `GET` | `/customers` | List customers in your org |
| `POST` | `/customers` | Create a customer (auto-creates default AI policy) |
| `GET` | `/customers/{id}` | Get one customer |
| `PUT` | `/customers/{id}` | Update a customer |
| `GET` | `/customers/{id}/ai-policy` | Get the customer AI policy |
| `PUT` | `/customers/{id}/ai-policy` | Update the policy |

AI policy body:
```json
{
  "external_ai_allowed": true,
  "preferred_provider": "ollama",
  "fallback_allowed": true,
  "redact_pii_before_ai": true,
  "store_ai_outputs": true,
  "local_only_mode": false
}
```

---

## Alerts

### `POST /alerts`
```json
{ "title": "C2 Beacon", "raw_payload": "{...}", "source_tool": "Suricata", "severity": "Critical", "customer_id": 2 }
```
`raw_payload` may be free text or JSON (auto-detected). Returns the created `Alert`.

### `GET /alerts`
Query params: `status`, `customer_id`, `limit`. Returns `Alert[]`.

### `GET /alerts/{id}`
Returns `AlertDetail` including `normalized`, `entities[]`, `iocs[]`.

### Pipeline (all `POST`)
| Path | Description |
|---|---|
| `/alerts/{id}/parse` | Normalize → entities + IOCs, detect category |
| `/alerts/{id}/enrich` | Enrich IOCs (mock + configured providers) |
| `/alerts/{id}/correlate` | Find related alerts; returns `{ matches, correlation_count, prior_verdicts }` |
| `/alerts/{id}/investigate` | Run the multi-agent investigation; body `{ "provider": "mock", "routing_mode": "auto", "auto_pipeline": true }` → returns `Investigation` |
| `/alerts/{id}/generate-report` | Render the markdown report → returns `Report` |

---

## Investigations

| Method | Path | Description |
|---|---|---|
| `GET` | `/investigations` | List investigations |
| `GET` | `/investigations/{id}` | Full investigation incl. `result` JSON |
| `POST` | `/investigations/{id}/feedback` | Body `{ "label": "TP", "comment": "confirmed" }` |

Verdict values: `True Positive`, `False Positive`, `Benign Authorized Activity`, `Duplicate`, `Needs Review`, `Escalated`.

---

## Reports

| Method | Path | Description |
|---|---|---|
| `GET` | `/reports` | List reports |
| `GET` | `/reports/{id}` | Report metadata + markdown |
| `GET` | `/reports/{id}/markdown` | Raw markdown (text/plain) |
| `POST` | `/reports/{id}/regenerate` | Re-render from the latest investigation |

---

## AI

| Method | Path | Description |
|---|---|---|
| `GET` | `/ai/providers` | Providers + config (default, routing mode, fallback chain, flags) |
| `GET` | `/ai/providers/health` | Live health check of configured providers |
| `POST` | `/ai/providers/test` | Body `{ "provider": "ollama", "model": "llama3.1" }` |
| `GET` | `/ai/runs` | Last N AI runs (cost/latency/tokens) |
| `GET` | `/ai/usage-summary` | Aggregated usage, cost, local vs cloud, by provider/model |
| `POST` | `/ai/prompt-preview` | Body `{ "prompt_type": "soc_investigation", "sample_text": "..." }` |

---

## Dashboard

| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard/summary` | Totals, severity/status/verdict/category breakdowns |
| `GET` | `/dashboard/daily-summary` | 24h narrative + highlights |
| `GET` | `/dashboard/mitre-summary` | Tactic/technique counts |
| `GET` | `/dashboard/ai-operations` | Provider usage, cost, latency, fallback, recent runs |

---

## Playbooks · Allowlists · Audit

| Method | Path | Description |
|---|---|---|
| `GET` | `/playbooks` | List built-in playbooks |
| `GET` | `/playbooks/{id}` | One playbook (triage/investigation/containment steps, MITRE) |
| `GET` | `/allowlists` | List allowlist entries (`?customer_id=`) |
| `POST` | `/allowlists` | Body `{ "customer_id": 2, "entry_type": "ip", "value": "192.168.143.84", "reason": "scanner" }` |
| `DELETE` | `/allowlists/{id}` | Remove an entry |
| `GET` | `/audit-logs` | Audit trail (`?action=`, `?limit=`) |

---

## Investigation result schema

`investigation.result` follows this structure (abbreviated):

```json
{
  "executive_summary": "", "technical_analysis": "",
  "verdict": "True Positive", "confidence_score": 80,
  "severity_recommendation": "Critical", "reasoning_summary": "",
  "facts_observed": [], "assumptions": [], "evidence": [],
  "missing_evidence": [], "ioc_summary": [], "mitre_mapping": [],
  "timeline": [], "recommended_actions": [
    { "action": "...", "priority": "high", "requires_human_approval": true, "reason": "..." }
  ],
  "customer_email_draft": "", "ticket_update": "",
  "investigation_checklist": [],
  "detection_query_suggestions": {
    "splunk": "", "crowdstrike_logscale": "", "wazuh": "",
    "elastic_kql": "", "sigma": "", "sentinel_kql": ""
  },
  "qa_warnings": []
}
```
