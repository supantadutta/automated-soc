.PHONY: up down logs seed test migrate backend frontend build ps clean install-backend

COMPOSE = docker compose

up: ## Build and start the full stack
	$(COMPOSE) up --build -d
	@echo "Backend:  http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"

up-local-llm: ## Start the stack with the Ollama local-LLM profile
	$(COMPOSE) -f docker-compose.yml -f docker-compose.local-llm.yml up --build -d

down: ## Stop and remove containers
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show service status
	$(COMPOSE) ps

seed: ## Seed demo data (admin user, customers, 20 sample alerts)
	$(COMPOSE) exec backend python -m app.db.seed

migrate: ## Run Alembic migrations inside the backend container
	$(COMPOSE) exec backend alembic upgrade head

test: ## Run the backend test suite inside the container
	$(COMPOSE) exec backend python -m pytest -q

backend: ## Run the backend locally (requires venv + Postgres or sqlite)
	cd backend && uvicorn app.main:app --reload --port 8000

frontend: ## Run the frontend locally
	cd frontend && npm run dev

install-backend: ## Create venv and install backend deps
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

clean: ## Remove containers and volumes
	$(COMPOSE) down -v

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
