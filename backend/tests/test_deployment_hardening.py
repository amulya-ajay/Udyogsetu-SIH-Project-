"""Security/deployment hardening tests.

Covers production defaults that protect the deployed deployment:
- CORS restricts origins to the configured allow-list (no wildcard).
- CORS preflight (OPTIONS) responds with the expected origin headers.
- The app refuses to start when DEBUG=false with a missing/forbidden
  JWT secret so production never silently falls back to a weak secret.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import normalize_database_url
from app.main import app

client = TestClient(app)


def test_cors_blocks_disallowed_origin():
    """Requests with a foreign Origin must NOT receive CORS grant headers."""
    resp = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert "access-control-allow-origin" not in resp.headers


def test_cors_allows_trusted_local_origin_preflight():
    """OPTIONS preflight from a configured origin returns the expected grant."""
    origin = "http://localhost:3000"
    resp = client.options(
        "/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == origin


def test_production_fails_fast_without_jwt_secret():
    """ENVIRONMENT=production with a missing JWT secret must fail validation."""
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="")


def test_production_rejects_forbidden_weak_secret():
    """Weak/placeholder JWT secrets must not be accepted for production."""
    for weak in ("secret", "changeme", "test-secret", "default-secret"):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="production", JWT_SECRET_KEY=weak)


def test_normalize_database_url_handles_railway_format():
    """A driver-less postgresql:// URL (Railway) gains the asyncpg driver."""
    assert (
        normalize_database_url("postgresql://user:pw@host:5432/db")
        == "postgresql+asyncpg://user:pw@host:5432/db"
    )
    assert (
        normalize_database_url("postgres://user:pw@host:5432/db")
        == "postgresql+asyncpg://user:pw@host:5432/db"
    )


def test_normalize_database_url_preserves_explicit_drivers_and_others():
    """Explicit asyncpg URLs and non-PostgreSQL URLs are left unchanged."""
    assert (
        normalize_database_url("postgresql+asyncpg://u:p@h/db")
        == "postgresql+asyncpg://u:p@h/db"
    )
    assert (
        normalize_database_url("sqlite+aiosqlite:///tmp/test.db")
        == "sqlite+aiosqlite:///tmp/test.db"
    )
