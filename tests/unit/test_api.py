"""Integration tests for Atlas API endpoints."""

import pytest
from fastapi.testclient import TestClient

from atlas.api.main import app


@pytest.fixture
def client():
    """Create a test client for the Atlas API."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestSecurityEndpoint:
    """Tests for the /v1/security endpoint."""

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
    """Tests for the /v1/model endpoint."""

    def test_model_info(self, client: TestClient) -> None:
        response = client.get("/v1/model")
        assert response.status_code == 200
        data = response.json()
        assert "model_type" in data or "model" in data


class TestAuthEndpoints:
    """Tests for the /api/auth/* endpoints."""

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

    def test_register_and_login(self, client: TestClient) -> None:
        reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "test@atlas.sa",
                "password": "TestPass1",
                "confirm_password": "TestPass1",
                "full_name": "Test User",
            },
        )
        assert reg_response.status_code == 200
        data = reg_response.json()
        assert data["user"]["role"] == "viewer"

    def test_register_duplicate_email(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "demo@atlas.sa",
                "password": "TestPass1",
                "confirm_password": "TestPass1",
                "full_name": "Dup User",
            },
        )
        assert response.status_code == 409

    def test_get_user_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/auth/user")
        assert response.status_code == 401

    def test_get_user_with_token(self, client: TestClient) -> None:
        login = client.post(
            "/api/auth/login",
            json={"email": "demo@atlas.sa", "password": "Demo@123"},
        )
        token = login.json()["access_token"]
        response = client.get(
            "/api/auth/user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "demo@atlas.sa"

    def test_logout_revokes_token(self, client: TestClient) -> None:
        login = client.post(
            "/api/auth/login",
            json={"email": "demo@atlas.sa", "password": "Demo@123"},
        )
        token = login.json()["access_token"]

        # Logout
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200

        # Token should now be revoked
        user_resp = client.get(
            "/api/auth/user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user_resp.status_code == 401


class TestChatEndpoint:
    """Tests for the /v1/chat endpoint."""

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

    def test_chat_sanitizes_null_bytes(self, client: TestClient) -> None:
        response = client.post(
            "/v1/chat",
            json={"question": "Show \x00me all customers"},
        )
        # Should succeed after sanitization
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_security_headers_present(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_api_no_cache(self, client: TestClient) -> None:
        response = client.get("/v1/security")
        assert "no-store" in response.headers.get("Cache-Control", "")


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_headers(self, client: TestClient) -> None:
        # First request should succeed
        response = client.get("/health")
        assert response.status_code == 200
