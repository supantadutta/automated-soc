"""AutoSOC Command Center — FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ALL_ROUTERS
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.base import Base
from app.db.session import engine

configure_logging("DEBUG" if settings.debug else "INFO")
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup for a smooth local-first experience. In production
    # use Alembic migrations (see alembic/).
    try:
        import app.models  # noqa: F401  ensure metadata is populated
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ready.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not create tables at startup: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered SOC automation for alert triage, investigation, "
    "enrichment, reporting, and safe response guidance.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "default_provider": settings.default_ai_provider,
        "routing_mode": settings.ai_routing_mode,
    }


@app.get("/", tags=["system"])
def root():
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}


for router in ALL_ROUTERS:
    app.include_router(router)
