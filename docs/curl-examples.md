# Sample cURL Commands

Base URL `http://localhost:8000`. Set a token first:

```bash
export BASE=http://localhost:8000
export TOKEN=$(curl -s $BASE/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@autosoc.local","password":"Admin123!"}' | jq -r .access_token)
auth() { curl -s -H "Authorization: Bearer $TOKEN" "$@"; }
```

## Health & auth
```bash
curl -s $BASE/health | jq
auth $BASE/auth/me | jq
```

## Submit and investigate an alert
```bash
# Create
ALERT=$(auth -X POST $BASE/alerts -H 'Content-Type: application/json' -d '{
  "raw_payload":"{\"alert_name\":\"C2 Beacon\",\"source_tool\":\"Suricata\",\"severity\":\"Critical\",\"src_ip\":\"10.20.8.55\",\"domain\":\"beacon.evil-c2.example\"}",
  "source_tool":"Suricata","severity":"Critical"
}')
ID=$(echo "$ALERT" | jq -r .id)

# Pipeline
auth -X POST $BASE/alerts/$ID/parse | jq '.category'
auth -X POST $BASE/alerts/$ID/enrich | jq '.iocs'
auth -X POST $BASE/alerts/$ID/correlate | jq
auth -X POST $BASE/alerts/$ID/investigate -H 'Content-Type: application/json' \
  -d '{"provider":"mock","routing_mode":"offline_demo"}' | jq '{verdict,confidence_score}'
auth -X POST $BASE/alerts/$ID/generate-report | jq '.id'
```

## AI gateway
```bash
# Provider list with capability + privacy metadata
auth $BASE/ai/providers | jq '.providers[] | {provider,privacy_level,latency_class,configured}'

# Model capability registry
auth $BASE/ai/capabilities | jq '.models[] | {model,provider,privacy_level,max_context_tokens}'

# Live health checks (configured providers only)
auth $BASE/ai/providers/health | jq

# Test one provider
auth -X POST $BASE/ai/providers/test -H 'Content-Type: application/json' \
  -d '{"provider":"ollama","model":"llama3.1"}' | jq

# Locally installed Ollama models
auth $BASE/ai/ollama/models | jq
```

## Runtime routing config (org admin)
```bash
auth $BASE/ai/config | jq
auth -X PUT $BASE/ai/config -H 'Content-Type: application/json' \
  -d '{"default_provider":"ollama","routing_mode":"local_only"}' | jq
```

## Prompt management
```bash
auth $BASE/ai/prompts | jq '.[] | {prompt_type,version,is_active}'
NEW=$(auth -X POST $BASE/ai/prompts -H 'Content-Type: application/json' \
  -d '{"prompt_type":"soc_investigation","template":"Evidence-based JSON. Include confidence. Human approval required.","name":"custom v2"}')
PID=$(echo "$NEW" | jq -r .id)
auth -X POST $BASE/ai/prompts/$PID/test | jq        # eval score
auth -X POST $BASE/ai/prompts/$PID/activate | jq
```

## Observability & dashboards
```bash
auth $BASE/ai/usage-summary | jq
auth $BASE/dashboard/ai-operations | jq '{total_runs,estimated_cost,timeseries,top_expensive_investigations}'
auth $BASE/dashboard/summary | jq
auth "$BASE/audit-logs?action=ai.config.update" | jq
```
