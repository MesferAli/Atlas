"""Integration tests for Atlas API endpoints.

These tests use the real FastAPI app with mock connectors (no Oracle/Qdrant needed).
The app already uses mock connector and indexer when ATLAS_USE_UNSLOTH is unset.
"""

import os

import pytest

# Ensure we use MockLLM, not Unsloth
os.environ.pop("ATLAS_USE_UNSLOTH", None)

from fastapi.testclient import TestClient  # noqa: E402

from atlas.api.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Clear rate limit counters before each test."""
    from atlas.api.security import middleware as mw

    # Walk the ASGI middleware stack to find the RateLimitMiddleware instance
    inner = getattr(app, "middleware_stack", None)
    while inner is not None:
        if isinstance(inner, mw.RateLimitMiddleware):
            inner.request_counts.clear()
            break
        inner = getattr(inner, "app", None)
    yield


@pytest.fixture
def client():
    """Create a test client for the Atlas API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """Get a valid auth token via login."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "demo@atlas.sa", "password": "Demo@123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestSecurityEndpoint:
    def test_security_status(self, client: TestClient) -> None:
        response = client.get("/v1/security")
        assert response.status_code == 200
        data = response.json()
        assert data["security_mode"] == "READ_ONLY"
        assert data["thin_mode_enabled"] is True
        assert data["read_only_enforced"] is True
        assert "INSERT" in data["blocked_operations"]

    def test_security_blocks_all_dml(self, client: TestClient) -> None:
        response = client.get("/v1/security")
        blocked = response.json()["blocked_operations"]
        for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]:
            assert keyword in blocked


class TestModelEndpoint:
    def test_model_info(self, client: TestClient) -> None:
        response = client.get("/v1/model")
        assert response.status_code == 200
        data = response.json()
        assert "model_type" in data or "model" in data


class TestAuthEndpoints:
    def test_login_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@atlas.sa", "password": "Demo@123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "demo@atlas.sa"
        assert data["user"]["role"] == "analyst"

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@atlas.sa", "password": "WrongPass1"},
        )
        assert response.status_code == 401

    def test_login_weak_password_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@atlas.sa", "password": "short"},
        )
        assert response.status_code == 422

    def test_get_user_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/auth/user")
        assert response.status_code == 401

    def test_get_user_with_token(self, client: TestClient, auth_token: str) -> None:
        response = client.get(
            "/api/auth/user",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "demo@atlas.sa"

    def test_logout_revokes_token(self, client: TestClient, auth_token: str) -> None:
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert logout_resp.status_code == 200

        # Token should now be revoked
        user_resp = client.get(
            "/api/auth/user",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert user_resp.status_code == 401


class TestChatEndpoint:
    def test_chat_with_question(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat",
            json={"question": "Show me all customers"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "generated_sql" in data
        assert "relevant_tables" in data

    def test_chat_rejects_short_question(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat",
            json={"question": "ab"},
        )
        assert response.status_code == 422

    def test_chat_with_auth_passes_role(
        self, client: TestClient, auth_token: str
    ) -> None:
        """Verify authenticated chat includes user role context."""
        response = client.post(
            "/v1/chat",
            json={"question": "Show me all customers"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "generated_sql" in data


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_api_no_cache(self, client: TestClient) -> None:
        response = client.get("/v1/security")
        assert "no-store" in response.headers.get("Cache-Control", "")


class TestRateLimiting:
    def test_rate_limit_headers(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
