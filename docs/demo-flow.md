# Demo Flow

A 5-minute scripted walkthrough using the seeded data and the offline **mock** provider (no API keys required).

## 0. Start & log in

```bash
make up           # or: cd backend && python -m app.db.seed && uvicorn app.main:app --reload
```

Open http://localhost:3000 and sign in:

```
admin@autosoc.local / Admin123!
```

The backend seeds **20 realistic alerts** across two customers (*Globex*, *Initech*), plus allowlists, a known false positive, and 13 playbooks.

## 1. Dashboard

Land on **Dashboard**. Note the severity breakdown, verdict distribution (after you run investigations), top categories, and MITRE tactics. Click **Submit Alert** to see the intake form.

## 2. Investigate a true positive (malicious IOC)

1. Go to **Alerts** → open **"C2 Domain Communication Detected"** (Suricata, Critical).
2. On the pipeline bar run, in order: **1. Parse → 2. Enrich → 3. Correlate**.
   - *Parse* extracts `src_ip`, `dest_ip`, and the domain `beacon.evil-c2.example`; category becomes `c2`.
   - *Enrich* flags `beacon.evil-c2.example` and `203.0.113.66` as **malicious** (mock matches the known-bad markers).
3. Leave the provider selector on **Auto** (or pick `mock`) and click **4. Investigate**.
   - Verdict: **True Positive**, confidence ~80% — driven by the confirmed malicious IOC. The verdict engine elevates this independently of the LLM.
4. Open the **AI Investigation** tab: executive summary, evidence, missing evidence, recommended actions (all flagged *human approval required*), and QA warnings.
5. Open **MITRE** (T1071 Command and Control) and **Detection Queries** (Splunk, LogScale, Wazuh, Elastic KQL, Sigma, Sentinel KQL).
6. Click **5. Generate Report**, then the **Report** tab for the full markdown SOC report with customer email draft and ticket note.

## 3. See an evidence-based "Needs Review"

1. Open **"Suspicious Active Directory Authentication Activity"** (CrowdStrike, Globex).
2. Run **Parse → Enrich → Investigate**.
   - The source `192.168.143.84` is on Globex's **allowlist** (sanctioned scanner) and there's no malicious IOC, so the verdict lands on **Benign Authorized Activity** / **Needs Review** with the allowlist hit cited.
3. This demonstrates the platform never claiming a compromise without evidence.

## 4. AI Operations

Go to **AI Operations**:
- Total runs, average latency, estimated cost (≈ $0 for mock/local), failed/fallback counts.
- **Local vs Cloud** split and **Requests by Provider**.
- **Last 20 AI Runs** table.

## 5. Switch to a local LLM (optional, private)

Stop the stack, set in `.env`:

```env
DEFAULT_AI_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
AI_FALLBACK_CHAIN=ollama,mock
```

```bash
make up-local-llm
docker exec -it autosoc-command-center-ollama-1 ollama pull llama3.1
```

Re-investigate any alert — the investigation now runs entirely on your machine. Set a customer's **local-only mode** (Customers → customer → AI Policy) to *guarantee* no external calls for that tenant.

## 6. Analyst feedback loop

On any investigated alert, open the **Feedback** tab (or the **Feedback** page) and record **TP / FP / Benign / Duplicate / Escalated / Customer Confirmed**. Feedback is audit-logged and feeds future correlation/confidence.

## 7. Audit trail

Open **Audit Log** to see every action (login, parse, enrich, investigate, report, feedback) with actor and timestamp — tenant-isolated.
