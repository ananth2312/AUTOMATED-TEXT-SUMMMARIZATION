"""
tests/conftest.py
──────────────────
Shared test fixtures for the FastAPI test suite.

Uses TestClient from httpx via FastAPI's built-in test utilities.
The test database is a separate MongoDB database (academic_research_test_db)
so it can be isolated from development data and cleaned between runs.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Point to test database BEFORE importing the app (settings cached at import time)
os.environ.setdefault("MONGODB_DB_NAME", "academic_research_test_db")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

from app.main import app
from app.database.connection import _client, connect_db, disconnect_db, get_db


@pytest.fixture(scope="session")
def test_client():
    """
    Create a TestClient with the FastAPI app.
    Starts the lifespan (connects DB) once per test session.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_test_db():
    """
    Drop test collections before each test to ensure isolation.
    Skips gracefully for pure unit tests that don't use the database.
    Only cleans the test database, never the dev/prod database.
    """
    from app.database.connection import _db as current_db
    if current_db is None:
        yield
        return
    for collection in ["users", "documents", "analyses", "audit_logs"]:
        current_db[collection].drop()
    yield
    for collection in ["users", "documents", "analyses", "audit_logs"]:
        current_db[collection].drop()


# ── Helper: create and auth a user ───────────────────────────────────────────

def register_and_login(client: TestClient, email: str = "test@example.com") -> str:
    """Register a user and return a Bearer token string."""
    client.post("/api/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "Testpass1",
    })
    resp = client.post("/api/auth/login", json={
        "email": email,
        "password": "Testpass1",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
