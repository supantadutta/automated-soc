# Local LLM Setup

AutoSOC Command Center is **local-first**: the entire SOC workflow — parsing,
enrichment, correlation, investigation/verdicts, and report generation — can run
against a model on your own hardware with **zero data egress**.

## Why run a local LLM?

- **Privacy / data residency.** Alerts, IOCs, host names, usernames, and case
  details never leave your network. Essential for regulated environments and for
  MSSP customers with `local_only_mode=true`.
- **Offline operation.** Air-gapped or DR scenarios keep working with no
  internet and no API keys.
- **No per-token cost.** Local inference is `$0` in the usage summary — you pay
  for hardware, not tokens.
- **Control.** You choose the exact model, quantization, and version, and you
  can pin a tenant to it permanently.

The platform supports four local paths: **Ollama**, **LM Studio**, **vLLM**, and
any **generic OpenAI-compatible** server. All four are interchangeable from the
application's perspective. See [ai-providers.md](./ai-providers.md) for the full
provider matrix and routing details.

---

## Ollama (recommended default)

Ollama is the simplest local option and the recommended local-first default.

1. **Install** from <https://ollama.com/download> (macOS, Linux, Windows).
   On Linux:

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start the server** (it usually runs as a service after install; otherwise
   run it manually):

   ```bash
   ollama serve
   ```

3. **Pull a chat model** and an **embedding model** (embeddings power the
   correlation / vector-search features):

   ```bash
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

4. **Point the backend at Ollama** in `.env`:

   ```env
   AI_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434     # use http://ollama:11434 inside Docker Compose
   OLLAMA_MODEL=llama3.1

   AI_EMBEDDING_PROVIDER=ollama
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```

5. **Verify** the model responds:

   ```bash
   curl http://localhost:11434/api/tags          # lists pulled models
   ollama run llama3.1 "Summarize an SSH brute-force alert in one sentence."
   ```

> **Docker note.** When the backend runs in Docker Compose and Ollama runs as a
> sibling container (see [docker-compose.local-llm.yml](#docker-composelocal-llmyml)),
> use `OLLAMA_BASE_URL=http://ollama:11434` (the service name), **not**
> `localhost`.

---

## LM Studio

LM Studio is a desktop app that exposes an OpenAI-compatible local server — handy
for quickly trying different GGUF models.

1. **Download** from <https://lmstudio.ai/> and install.
2. In the **Discover/Search** tab, download a model (e.g. a
   `Llama-3.1-8B-Instruct` GGUF), then **load** it.
3. Open **Developer → Local Server** and click **Start Server**. Note the port
   (default `1234`).
4. **Configure the backend** in `.env`:

   ```env
   AI_PROVIDER=lmstudio
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL=local-model     # the identifier shown in LM Studio's server tab
   ```

5. **Verify**:

   ```bash
   curl http://localhost:1234/v1/models
   ```

---

## vLLM

vLLM is a high-throughput, self-hosted inference server with an OpenAI-compatible
API — a good choice for production-grade local inference on a GPU box.

1. **Install** (use a GPU machine with a recent CUDA toolkit):

   ```bash
   pip install vllm
   ```

2. **Launch the OpenAI-compatible API server**:

   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model meta-llama/Meta-Llama-3.1-8B-Instruct \
     --host 0.0.0.0 \
     --port 8001
   ```

3. **Configure the backend** in `.env`:

   ```env
   AI_PROVIDER=vllm
   VLLM_BASE_URL=http://localhost:8001/v1
   VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
   ```

4. **Verify**:

   ```bash
   curl http://localhost:8001/v1/models
   ```

---

## Generic OpenAI-compatible endpoint

For any other local/self-hosted server that speaks the OpenAI `/v1`
chat-completions API — `llama.cpp`'s server, `text-generation-webui`,
TGI-compatible proxies, an internal gateway, etc. — use the generic adapter.

```env
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=http://192.168.10.20:8080/v1
OPENAI_COMPATIBLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx   # any non-empty token if the server ignores auth
OPENAI_COMPATIBLE_MODEL=my-local-model
```

Verify with:

```bash
curl http://192.168.10.20:8080/v1/models
```

---

## Switching provider in the UI

Once a local server is running and the env vars are set:

1. Open **Settings → AI Providers**.
2. Select **Ollama** (or LM Studio / vLLM / OpenAI-compatible).
3. Click **Test** — this calls `POST /ai/providers/test` and confirms the
   backend can reach the local server and get a completion. You should see a
   green status and a latency figure.
4. Click **Save** to set it as the default provider.
5. (Optional, for strict tenants) open a customer and set the AI policy
   `local_only_mode=true` so that tenant is **always** served by a local
   provider regardless of the global default.

---

## docker-compose.local-llm.yml

The repo ships an overlay compose file that adds a local Ollama service and
points the backend at it. Run it **on top of** the base compose file:

```bash
docker compose -f docker-compose.yml -f docker-compose.local-llm.yml up -d
```

This overlay:

- Adds an **`ollama`** service (image `ollama/ollama`) exposing port `11434`.
- Mounts a persistent **`ollama_data`** volume so pulled models survive restarts.
- Overrides the **backend** env to `AI_PROVIDER=ollama` and
  `OLLAMA_BASE_URL=http://ollama:11434` (the service name on the compose
  network).

Example `docker-compose.local-llm.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: autosoc-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    # --- Optional GPU acceleration (NVIDIA) ---
    # Requires the NVIDIA Container Toolkit on the host.
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: ["gpu"]

  backend:
    environment:
      AI_PROVIDER: ollama
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: llama3.1
      AI_EMBEDDING_PROVIDER: ollama
      OLLAMA_EMBEDDING_MODEL: nomic-embed-text
      # Final safety net so the workflow always completes:
      AI_FALLBACK_CHAIN: ollama,mock
    depends_on:
      ollama:
        condition: service_healthy

volumes:
  ollama_data:
```

After the stack is up, **pull the models into the running container** (one-time;
they persist in the `ollama_data` volume):

```bash
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
```

### Full-privacy mode

To guarantee no data ever leaves the host, combine the overlay above with
`local_only_mode` on the customer(s):

- **Per-tenant:** Settings → Customers → *(customer)* → AI Policy →
  set `local_only_mode=true` (and `external_ai_allowed=false`,
  `redact_pii_before_ai=true` if desired).
- **Whole deployment:** keep `AI_PROVIDER=ollama` with
  `AI_FALLBACK_CHAIN=ollama,mock` so there are **no external providers** in the
  chain at all.

With `local_only_mode=true`, the AIRouter removes every external provider from
the candidate set and serves the tenant exclusively from Ollama / LM Studio /
vLLM / Mock — see [ai-providers.md](./ai-providers.md#privacy-mode--per-customer-ai-policy).
