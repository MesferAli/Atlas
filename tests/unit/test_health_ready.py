"""Tests for the deep health check endpoint."""

import os

import pytest

os.environ.pop("ATLAS_USE_UNSLOTH", None)

from fastapi.testclient import TestClient  # noqa: E402

from atlas.api.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    from atlas.api.security import redis_backend, token_blacklist

    redis_backend._rate_limiter = None
    redis_backend._token_bl = None
    token_blacklist._token_blacklist = None
    from atlas.api.security import middleware as mw

    fresh_rl = redis_backend.get_rate_limiter()
    inner = getattr(app, "middleware_stack", None)
    while inner is not None:
        if isinstance(inner, mw.RateLimitMiddleware):
            inner._backend = fresh_rl
            break
        inner = getattr(inner, "app", None)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestReadinessCheck:
    def test_readiness_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert "checks" in data

    def test_readiness_checks_agent(self, client: TestClient) -> None:
        resp = client.get("/health/ready")
        data = resp.json()
        assert data["checks"]["agent"]["status"] == "up"

    def test_readiness_checks_oracle(self, client: TestClient) -> None:
        resp = client.get("/health/ready")
        data = resp.json()
        assert data["checks"]["oracle"]["status"] == "up"
        assert data["checks"]["oracle"]["mode"] == "mock"

    def test_readiness_checks_qdrant(self, client: TestClient) -> None:
        resp = client.get("/health/ready")
        data = resp.json()
        assert data["checks"]["qdrant"]["status"] == "up"

    def test_api_version_header(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.headers.get("X-API-Version") == "1.0"
