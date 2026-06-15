# Deployment

## Docker Compose (recommended)

```bash
cp .env.example .env
make up            # build + start all services, backend auto-seeds demo data
```

Services started by `docker-compose.yml`:

| Service | Image / Build | Port | Notes |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | primary DB, healthchecked |
| `redis` | redis:7-alpine | 6379 | Celery broker/result backend |
| `qdrant` | qdrant/qdrant | 6333 | vector memory (optional) |
| `backend` | `./backend` | 8000 | FastAPI; runs `python -m app.db.seed` then uvicorn |
| `celery-worker` | `./backend` | — | async pipeline tasks |
| `frontend` | `./frontend` | 3000 | Next.js standalone build |

### Local LLM overlay

```bash
make up-local-llm   # adds the ollama service and points the backend at it
docker exec -it autosoc-command-center-ollama-1 ollama pull llama3.1
```

## Make targets

| Target | Action |
|---|---|
| `make up` | Build & start the stack |
| `make up-local-llm` | Start with the Ollama profile |
| `make down` | Stop & remove containers |
| `make logs` | Tail all logs |
| `make ps` | Service status |
| `make seed` | Re-run demo seeding |
| `make migrate` | `alembic upgrade head` in the backend container |
| `make test` | Run the backend test suite in-container |
| `make backend` / `make frontend` | Run a service locally |
| `make clean` | Stop & remove volumes |

## Running without Docker

### Backend
```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
# SQLite (no Postgres needed):
export DATABASE_URL="sqlite+pysqlite:///./autosoc.db"
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
pytest -q          # 24 tests, fully offline
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

## Database & migrations

- For local-first convenience the backend calls `Base.metadata.create_all` on startup and in the seed script.
- For production, use **Alembic**:
  ```bash
  alembic upgrade head            # applies 0001_initial (full schema)
  alembic revision --autogenerate -m "change"   # subsequent migrations
  ```
- Switch databases with `DATABASE_URL` (PostgreSQL recommended; SQLite supported for dev/test).

## Configuration

All configuration is environment-driven (`backend/app/core/config.py`). Copy `.env.example` → `.env`. The stack runs with **zero external keys** using the mock provider; add provider/enrichment keys only for the integrations you want.

## Scaling notes

- The API is stateless — run multiple `backend` replicas behind a load balancer.
- Offload long pipelines to `celery-worker` via `autosoc.process_alert` (parse → enrich → investigate → report).
- Point `AI_FALLBACK_CHAIN` at a fast local model first for cost control, with a premium cloud model as fallback for critical alerts (`soc_critical` routing mode).
