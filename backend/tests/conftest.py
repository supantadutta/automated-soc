"""Test fixtures. Uses an in-memory SQLite DB and the mock AI provider so the
full suite runs offline with no external services."""
from __future__ import annotations

import os

# Configure environment BEFORE importing app modules (settings are cached).
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DEFAULT_AI_PROVIDER", "mock")
os.environ.setdefault("AI_FALLBACK_CHAIN", "mock")
os.environ.setdefault("AI_ROUTING_MODE", "offline")
os.environ.setdefault("JWT_SECRET", "test-secret-key-test-secret-key-32b")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.session as db_session
from app.db.base import Base
import app.models  # noqa: F401

# Single shared in-memory connection for the whole test session.
_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)

# Patch the app's engine/session to use the test database.
db_session.engine = _engine
db_session.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    from app.main import app

    def _get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[db_session.get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    # Register a fresh org admin and return bearer headers.
    email = "tester@autosoc.local"
    client.post("/auth/register", json={
        "email": email, "password": "Test1234!", "full_name": "Tester",
        "organization_name": "Test Org",
    })
    resp = client.post("/auth/login", json={"email": email, "password": "Test1234!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
