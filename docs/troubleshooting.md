# Troubleshooting

## The app won't start

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` to Postgres | DB not ready | `make ps`; wait for `postgres` healthcheck, or use `DATABASE_URL=sqlite+pysqlite:///./autosoc.db` |
| Frontend shows "cannot reach API" | Backend down / wrong URL | Check `NEXT_PUBLIC_API_URL`; confirm `curl localhost:8000/health` |
| 401 redirect loop | Expired/invalid JWT | Log out and back in; verify `JWT_SECRET` unchanged between restarts |
| `value is not a valid email address` on register | strict TLD | Email is a plain string by design; any `user@host` works including `.local` |

## AI / provider issues

| Symptom | Cause | Fix |
|---|---|---|
| Every investigation uses `mock` | No provider keys / offline mode | Set `DEFAULT_AI_PROVIDER` + the provider's key in `.env`, or `PUT /ai/config` |
| Provider shows "not configured" | Missing env key | Add the key (e.g. `OPENAI_API_KEY`); see `docs/ai-providers.md` |
| `provider not configured` then `mock` used | Fallback chain kicked in | Expected — the chain always ends at `mock`. Check `/dashboard/ai-operations` → fallback events |
| Investigation verdict is always "Needs Review" | Weak/incomplete model output | The reliability layer forces this when evidence is missing; check `qa_warnings` in the result |
| AI output isn't valid JSON | Model ignored JSON instruction | The agent auto-repairs + retries with a stricter prompt, then falls back to mock — no action needed |
| Ollama models endpoint empty | No models pulled | `ollama pull llama3.1`; verify `OLLAMA_BASE_URL` |
| Ollama "unreachable" | Ollama not running / wrong host in Docker | Use `make up-local-llm` (sets `OLLAMA_BASE_URL=http://ollama:11434`) |
| Cost shows $0 | Local/mock providers are free | Expected. Cloud runs populate cost from the capability registry |

## Routing policies

Accepted values for `routing_mode` / `AI_ROUTING_MODE` (public name → internal):
`auto`, `cost_optimized`→cost, `quality_optimized`→quality, `privacy_optimized`/`local_only`→privacy, `speed_optimized`→speed, `critical_alert_mode`→soc_critical, `offline_demo`→offline. Unknown values fall back to `auto`.

## Privacy & data residency

- To guarantee no external calls for a tenant: **Customers → customer → AI Policy → Local-only mode** (or `external_ai_allowed=false`). The router filters the chain to local providers only.
- PII is redacted before any external provider call when `AI_ENABLE_PII_REDACTION=true` (default). IPs/hostnames are preserved as SOC indicators — use local-only mode for stricter handling.

## Database & migrations

| Symptom | Fix |
|---|---|
| Tables missing | Startup runs `create_all`; or `make migrate` / `alembic upgrade head` |
| Want a clean slate | `make clean` (drops volumes), then `make up` |
| Seed didn't load | `make seed` or `python -m app.db.seed` (idempotent) |

## Tests

```bash
cd backend && . .venv/bin/activate && pytest -q     # 40 tests, fully offline (sqlite + mock)
```
A harmless `error reading bcrypt version` warning from passlid/bcrypt 4.x may appear; it is trapped and does not affect functionality.

## Still stuck?

- Backend logs: `make logs` (secrets are auto-redacted).
- Interactive API explorer: `http://localhost:8000/docs`.
- Inspect AI runs: `GET /ai/runs` and `GET /dashboard/ai-operations`.
