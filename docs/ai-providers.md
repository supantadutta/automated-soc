# AI Providers

AutoSOC Command Center is **local-first** and **provider-agnostic**. Every AI
operation in the platform (alert parsing, IOC enrichment summarization,
correlation reasoning, investigation/verdict generation, report writing, and
embeddings for vector search) flows through a single **multi-provider AI
abstraction** so that you can run the entire SOC workflow against a fully local
model, a commercial frontier model, or any mix of the two — without changing a
line of application code.

This document covers:

- How the AI abstraction and **AIRouter** work
- Setup for every supported provider (env vars, models, local vs external)
- Fallback chains and what triggers them
- Routing modes (cost / quality / privacy / speed / soc-critical / offline)
- Privacy mode and per-customer AI policy
- Cost & token tracking
- Switching providers in the UI

---

## The multi-provider abstraction & AIRouter

The platform never talks to a vendor SDK directly. Instead, all callers request
a capability ("complete this prompt", "embed this text") from the AI
abstraction layer, which exposes a uniform interface across every provider:

```
SOC workflow (parse / enrich / correlate / investigate / report / embed)
        │
        ▼
   AIRouter  ──►  routing mode + per-customer AI policy
        │
        ▼
  Provider adapter (OpenAI │ Azure │ Anthropic │ Gemini │ Mistral │ Cohere │
                    Groq │ OpenRouter │ OpenAI-compatible │ Ollama │
                    LM Studio │ vLLM │ Mock)
```

The **AIRouter** is responsible for:

1. **Selection** — choosing which provider to use for a given request, based on
   the active routing mode and the customer's AI policy.
2. **Fallback** — if the chosen provider fails (timeout, error, rate limit, or a
   policy block), automatically trying the next provider in the configured
   fallback chain.
3. **Policy enforcement** — refusing to route sensitive data to external
   providers when a customer has `external_ai_allowed=false` or
   `local_only_mode=true`, and applying PII redaction when
   `redact_pii_before_ai=true`.
4. **Accounting** — capturing per-run token usage and cost for every call (see
   [Cost tracking](#cost-tracking)).

Each provider adapter normalizes requests and responses, maps the
platform-internal model alias to a concrete vendor model id, and reports tokens
and cost back to the router.

---

## Provider setup

> **Convention.** Every provider uses a consistent env var scheme:
> `*_API_KEY`, `*_MODEL`, and (where applicable) `*_BASE_URL` /
> `*_ENDPOINT`. The platform-wide default provider is selected with
> `AI_PROVIDER` and the embedding provider with `AI_EMBEDDING_PROVIDER`.
> Set these in your `.env` file (see [deployment.md](./deployment.md)).

### OpenAI

- **Type:** External (cloud). Data leaves your environment — do not use for
  `local_only_mode` customers.
- **Get a key:** <https://platform.openai.com/> → **API keys** → *Create new
  secret key*.
- **Env vars:**

  ```env
  OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  OPENAI_MODEL=gpt-4o
  OPENAI_BASE_URL=https://api.openai.com/v1   # optional override
  ```

- **Example models:** `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`,
  `text-embedding-3-large` (embeddings).

### Azure OpenAI

- **Type:** External (cloud, your Azure tenant). Data stays inside your Azure
  subscription/region but is still an external API — treat per your compliance
  posture.
- **Get credentials:** Azure Portal → your **Azure OpenAI** resource → *Keys and
  Endpoint*. Create a **deployment** of a model under **Model deployments**; the
  deployment name (not the base model name) is what you reference.
- **Env vars:**

  ```env
  AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  AZURE_OPENAI_ENDPOINT=https://my-soc-aoai.openai.azure.com
  AZURE_OPENAI_DEPLOYMENT=gpt-4o-soc
  AZURE_OPENAI_API_VERSION=2024-10-21
  ```

- **Example deployment/model:** a `gpt-4o` or `gpt-4o-mini` deployment.

### Anthropic Claude

- **Type:** External (cloud).
- **Get a key:** <https://console.anthropic.com/> → **API Keys** → *Create Key*.
- **Env vars:**

  ```env
  ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ANTHROPIC_MODEL=claude-opus-4-5
  ```

- **Example models:** `claude-opus-4-5` (highest quality, good for SOC-critical
  investigations), `claude-sonnet-*` (balanced cost/quality). **Use the exact
  model id available to your account** — model ids change over time, so confirm
  the current id in the Anthropic console before setting `ANTHROPIC_MODEL`.

### Google Gemini

- **Type:** External (cloud).
- **Get a key:** <https://aistudio.google.com/> → **Get API key**.
- **Env vars:**

  ```env
  GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  GEMINI_MODEL=gemini-1.5-pro
  ```

- **Example models:** `gemini-1.5-pro` (quality), `gemini-1.5-flash` (speed/cost).

### Mistral

- **Type:** External (cloud).
- **Get a key:** <https://console.mistral.ai/> → **API Keys**.
- **Env vars:**

  ```env
  MISTRAL_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  MISTRAL_MODEL=mistral-large-latest
  ```

- **Example models:** `mistral-large-latest`, `mistral-small-latest`.

### Cohere

- **Type:** External (cloud). Strong embeddings option.
- **Get a key:** <https://dashboard.cohere.com/api-keys>.
- **Env vars:**

  ```env
  COHERE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  COHERE_MODEL=command-r-plus
  ```

- **Example models:** `command-r-plus` (chat), `embed-english-v3.0`
  (embeddings).

### Groq

- **Type:** External (cloud). Very low latency — a good speed-mode target.
- **Get a key:** <https://console.groq.com/keys>.
- **Env vars:**

  ```env
  GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  GROQ_MODEL=llama-3.1-70b-versatile
  ```

- **Example models:** `llama-3.1-70b-versatile`, `llama-3.1-8b-instant`.

### OpenRouter

- **Type:** External (cloud gateway). Routes to many upstream models via one
  key; data egress depends on the chosen upstream model.
- **Get a key:** <https://openrouter.ai/keys>.
- **Env vars:**

  ```env
  OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
  OPENROUTER_MODEL=anthropic/claude-sonnet
  OPENROUTER_BASE_URL=https://openrouter.ai/api/v1   # optional override
  ```

- **Example models:** `anthropic/claude-sonnet`, `openai/gpt-4o`,
  `meta-llama/llama-3.1-70b-instruct`.

### Generic OpenAI-compatible

- **Type:** External **or** local, depending on where the endpoint runs. Use
  this adapter for any server that exposes the OpenAI `/v1` chat-completions
  API (self-hosted gateways, `llama.cpp` server, `text-generation-webui`,
  TGI-compatible proxies, etc.).
- **Get a base URL:** whatever your endpoint exposes.
- **Env vars:**

  ```env
  OPENAI_COMPATIBLE_BASE_URL=http://192.168.10.20:8080/v1
  OPENAI_COMPATIBLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx   # use any non-empty token if the server ignores auth
  OPENAI_COMPATIBLE_MODEL=my-local-model
  ```

- **Example models:** whatever your server has loaded, e.g.
  `Meta-Llama-3.1-8B-Instruct`.

### Ollama

- **Type:** **Local.** No data egress. Recommended for `local_only_mode`.
- **Get it:** <https://ollama.com/download>. See
  [local-llm-setup.md](./local-llm-setup.md) for the full walkthrough.
- **Env vars:**

  ```env
  OLLAMA_BASE_URL=http://localhost:11434      # http://ollama:11434 inside Docker Compose
  OLLAMA_MODEL=llama3.1
  ```

- **Example models:** `llama3.1`, `qwen2.5`, `mistral`; embeddings:
  `nomic-embed-text`.

### LM Studio

- **Type:** **Local.** No data egress. Exposes an OpenAI-compatible server.
- **Get it:** <https://lmstudio.ai/>. Load a model, then start the local server
  (**Developer → Local Server → Start**).
- **Env vars:**

  ```env
  LMSTUDIO_BASE_URL=http://localhost:1234/v1
  LMSTUDIO_MODEL=local-model   # the identifier shown in LM Studio's server tab
  ```

- **Example models:** any GGUF you load, e.g. a `Llama-3.1-8B-Instruct` build.

### vLLM

- **Type:** **Local / self-hosted.** No data egress when run on your own
  hardware. High-throughput OpenAI-compatible server.
- **Get it:** `pip install vllm`, then launch the OpenAI API server (see
  [local-llm-setup.md](./local-llm-setup.md)).
- **Env vars:**

  ```env
  VLLM_BASE_URL=http://localhost:8001/v1
  VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
  ```

- **Example models:** any HF model id vLLM can serve, e.g.
  `meta-llama/Meta-Llama-3.1-8B-Instruct`.

### Mock

- **Type:** **Local / built-in.** Deterministic, offline, **needs no
  configuration and no keys.**
- **Use it for:** demos, CI, and air-gapped smoke tests. Returns structured,
  realistic verdicts/reports without contacting any model. **Cost is always
  $0.**
- **Env vars:** none. Select it with `AI_PROVIDER=mock`.

---

## Fallback chains

The AIRouter tries providers **in order** until one succeeds. The chain is
configured with `AI_FALLBACK_CHAIN` (comma-separated provider keys):

```env
AI_PROVIDER=anthropic
AI_FALLBACK_CHAIN=anthropic,openai,groq,ollama,mock
```

A provider is skipped or fails over to the next when any of these occur:

| Trigger          | Description                                                              |
| ---------------- | ----------------------------------------------------------------------- |
| **Timeout**      | The provider did not respond within the configured request timeout.     |
| **Error**        | Network error, 5xx, malformed/invalid response, or auth failure.        |
| **Rate limit**   | HTTP 429 / quota exhaustion from the provider.                          |
| **Policy block** | The provider is external but the customer policy forbids external AI.    |

When a fallback occurs the router records which provider ultimately answered (so
the run's cost/token line reflects the real provider used). Putting a **local**
provider (`ollama`) and finally **`mock`** at the end of the chain guarantees
the workflow still completes even with no internet and no API keys.

---

## Routing modes

The active routing mode tells the AIRouter what to optimize for. It reorders the
candidate providers before applying the fallback logic.

| Mode             | Optimizes for                              | Prefers (typical order)                                  |
| ---------------- | ------------------------------------------ | -------------------------------------------------------- |
| **cost**         | Lowest $ per run                           | Mock → Ollama/local → Groq → mini/flash tiers → frontier |
| **quality**      | Best reasoning / accuracy                  | Anthropic (opus) → OpenAI (gpt-4o) → Gemini pro          |
| **privacy**      | No data egress                             | Local only: Ollama → LM Studio → vLLM → Mock             |
| **speed**        | Lowest latency                             | Groq → flash/mini tiers → local small models             |
| **soc-critical** | Highest-confidence verdicts for incidents  | Frontier models (Anthropic opus / OpenAI gpt-4o)         |
| **offline**      | Works with no internet                     | Local only: Ollama → LM Studio → vLLM → Mock             |

- **cost** and **speed** trade quality for efficiency — appropriate for
  high-volume parsing/enrichment.
- **quality** and **soc-critical** spend more for the strongest reasoning —
  appropriate for the investigation/verdict and report stages of confirmed
  incidents.
- **privacy** and **offline** restrict the candidate set to **local providers
  only**; external providers are removed entirely, regardless of the fallback
  chain.

---

## Privacy mode & per-customer AI policy

Each customer (tenant) carries an **AI policy** with three controls:

| Policy flag             | Effect                                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| `external_ai_allowed`   | When `false`, the router removes **all external/cloud providers** from the candidate set.      |
| `local_only_mode`       | When `true`, forces a privacy/offline posture: **only** Ollama, LM Studio, vLLM, and Mock.     |
| `redact_pii_before_ai`  | When `true`, PII (emails, usernames, host/user identifiers, etc.) is redacted before any call. |

How this constrains provider selection:

- `external_ai_allowed=false` **or** `local_only_mode=true` → the AIRouter
  filters the candidate list down to **local providers only**
  (`ollama`, `lmstudio`, `vllm`, `mock`). Any external provider configured in
  `AI_FALLBACK_CHAIN` is treated as a **policy block** and skipped.
- `redact_pii_before_ai=true` → applies the redaction pass to prompts *before*
  they are handed to any provider (local or external), so even local inference
  never sees raw PII.

This means a privacy-sensitive MSSP customer can be pinned to local inference
while other tenants on the same deployment use frontier cloud models — the
policy is evaluated **per request, per customer**.

> **Tip:** For a fully air-gapped tenant, set `local_only_mode=true` and ensure
> at least one local provider (Ollama) is healthy, with `mock` as the final
> fallback so the workflow always completes.

---

## Cost tracking

Every AI call records, per run:

- the **provider and model** that actually answered (after any fallback),
- **prompt / completion / total tokens**,
- the **computed cost** (token counts × the provider's per-token rate;
  local providers and Mock are `$0`),
- latency and success/failure.

Aggregate usage is exposed via the API:

```
GET /ai/usage-summary
```

Returns totals and breakdowns (by provider, by operation type, and over time):
total runs, total tokens, total cost, and average latency. The dashboard's **AI
Operations** panel renders this summary. Because Mock and local providers cost
`$0`, a demo or a `local_only_mode` tenant shows a $0 spend line while still
producing full token counts for local runs.

---

## Switching providers in the UI

1. Go to **Settings → AI Providers**.
2. Select a provider from the list and confirm its model/base URL.
3. Click **Test connection** — this issues `POST /ai/providers/test`, which
   performs a minimal round-trip to verify credentials/reachability and reports
   latency.
4. **Set as default** to make it the platform default (`AI_PROVIDER`), or
5. Open a customer and set its **per-customer AI policy** (`external_ai_allowed`,
   `local_only_mode`, `redact_pii_before_ai`) plus an optional preferred
   provider/routing mode for that tenant.

### Provider quick reference

| Provider               | Local / External | Needs key | Good for                                      |
| ---------------------- | ---------------- | --------- | --------------------------------------------- |
| OpenAI                 | External         | Yes       | Quality, broad capability                     |
| Azure OpenAI           | External         | Yes       | Enterprise/compliance in your Azure tenant    |
| Anthropic Claude       | External         | Yes       | SOC-critical, high-confidence investigations  |
| Google Gemini          | External         | Yes       | Quality (pro) or speed/cost (flash)           |
| Mistral                | External         | Yes       | Balanced cost/quality                         |
| Cohere                 | External         | Yes       | Strong embeddings, retrieval                  |
| Groq                   | External         | Yes       | Lowest latency (speed mode)                   |
| OpenRouter             | External         | Yes       | One key, many upstream models                 |
| OpenAI-compatible      | Local or Ext.    | Maybe     | Any self-hosted `/v1` server                  |
| Ollama                 | Local            | No        | Privacy / offline / local-first default       |
| LM Studio              | Local            | No        | Desktop local inference, easy model swapping  |
| vLLM                   | Local            | No        | High-throughput self-hosted inference         |
| Mock                   | Local (built-in) | No        | Demos, CI, air-gapped smoke tests ($0)        |
