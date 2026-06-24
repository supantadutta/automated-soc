# Security & Privacy

AutoSOC Command Center is a **defensive** security product. This document describes its scope and guardrails.

## Defensive-only scope

The platform assists with alert triage, investigation, enrichment, correlation, reporting, and **response guidance**. It deliberately does **not**:

1. Perform offensive exploitation.
2. Generate malware or attack tooling.
3. Execute destructive automation by default.
4. Automatically disable users.
5. Automatically block IPs.
6. Automatically delete files.
7. Automatically kill processes.

All response/containment actions are produced as **recommendations only** and are flagged `requires_human_approval=true`. The Report Writer and QA agents both enforce this; the QA agent flags any action that looks destructive but is not marked for approval.

## Evidence-based verdicts

- Every verdict lists **evidence** and **missing evidence**.
- The deterministic **verdict engine** (`verdict_service.py`) runs independently of the LLM:
  - Weak evidence (`< 2` strong indicators and no malicious IOC) → forced **Needs Review**.
  - Confirmed malicious IOC → supports **True Positive** with raised confidence.
  - Allowlist / known-FP match (without malicious IOC) → permits **Benign Authorized Activity**.
- The **QA Review agent** downgrades over-confident TP/FP claims lacking evidence.
- Every report includes a **confidence score**.

## Tenant isolation

- Data is scoped by `organization_id`; every tenant-scoped query is filtered to the authenticated user's organization (`TenantContext` + `scope_filter`).
- Customer records, alerts, investigations, reports, allowlists, and AI runs never cross organizations.
- MSSP mode nests customers under an organization, each with its own AI policy.

## Local-only / private AI

- Per-customer `local_only_mode` or `external_ai_allowed=false` forces the AIRouter to a **local-only chain** (`ollama → lmstudio → vllm → mock`). External providers are never attempted.
- The **Privacy Guard agent** and AIRouter both enforce this — defense in depth.

## PII redaction

- When `redact_pii_before_ai` (default on) is set, the AIRouter redacts emails, SSNs, card numbers, and obvious secrets/API keys from prompts **before any external provider call**.
- IP addresses and hostnames are intentionally preserved (they are essential SOC indicators); customers needing stricter handling should use local-only mode.

## Secrets handling

- API keys are read from environment variables only and are **never** returned to the frontend (the `/ai/providers` endpoint exposes only `configured: true/false`, model name, and health).
- Logs use a redacting formatter that masks anything resembling an API key, bearer token, or password.
- Provider error messages are normalized and never echo auth headers/keys; failures stored in `ai_runs.error_message` are redacted.

## Audit logging

- Every significant action (login, alert create/parse/enrich/correlate/investigate/report, feedback, allowlist changes, AI policy changes) is written to `audit_logs` with actor, target, and timestamp.
- Audit logs are tenant-scoped and viewable at **Audit Log** / `GET /audit-logs`.

## Authentication & RBAC

- JWT bearer auth (`python-jose`), bcrypt password hashing (`passlib`).
- **Access + refresh tokens.** `POST /auth/login` returns both. `POST /auth/refresh` exchanges a valid refresh token for a new access token.
- **Revocation.** Each user has a `token_version`; `POST /auth/logout` (and any password change) increments it, immediately invalidating all previously issued access/refresh tokens.
- **Role matrix** (enforced at the route layer):

  | Capability | viewer | analyst | soc_manager | org_admin | platform_admin |
  |---|:---:|:---:|:---:|:---:|:---:|
  | Read dashboards/alerts/reports | ✅ | ✅ | ✅ | ✅ | ✅ |
  | Submit alerts, investigate, feedback | | ✅ | ✅ | ✅ | ✅ |
  | Manage customers, allowlists, SOPs; **approve containment** | | | ✅ | ✅ | ✅ |
  | Org-wide AI config, user/role management | | | | ✅ | ✅ |
  | Cross-organization access | | | | | ✅ |

## Rate limiting & abuse protection

- In-process sliding-window rate limiter (`RATE_LIMIT_PER_MINUTE`, default 120/min per client IP; honors `X-Forwarded-For`). Returns `429` with `Retry-After`. Back it with Redis for multi-node.
- Alert `raw_payload` is capped at `MAX_ALERT_PAYLOAD_CHARS` (default 100k) — protects storage and AI token cost (`413` on overflow).

## Secrets at rest

- Provider/integration secrets supplied via environment variables are never written to the DB.
- Any secret that *is* persisted (e.g. a per-org key set through the API) is encrypted with Fernet (`app/core/crypto.py`, key from `SECRET_ENCRYPTION_KEY` or derived from `JWT_SECRET`) and only ever returned masked (`****1234`).

## Production hardening checklist

- [ ] Set a strong `JWT_SECRET` (≥32 bytes) and rotate the seed admin password.
- [ ] Terminate TLS at a reverse proxy; restrict `CORS_ORIGINS`.
- [ ] Use managed Postgres with backups; run Alembic migrations instead of `create_all`.
- [ ] Store provider keys in a secrets manager, not plain `.env`.
- [ ] Enable `local_only_mode` for regulated customers.
- [ ] Review audit logs and AI runs regularly.
