"""Tests for the token blacklist module."""

from datetime import datetime, timedelta, timezone

import pytest

from atlas.api.security.token_blacklist import TokenBlacklist


@pytest.fixture(autouse=True)
def _reset_blacklist():
    """Reset singletons before each test."""
    from atlas.api.security import redis_backend, token_blacklist

    redis_backend._token_bl = None
    token_blacklist._token_blacklist = None
    yield


class TestTokenBlacklist:
    """Tests for TokenBlacklist."""

    def test_revoke_and_check(self) -> None:
        bl = TokenBlacklist()
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        bl.revoke("jti_123", exp)
        assert bl.is_revoked("jti_123") is True
        assert bl.is_revoked("jti_other") is False

    def test_cleanup_expired(self) -> None:
        bl = TokenBlacklist()
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        bl.revoke("expired_jti", past)
        bl.revoke("active_jti", future)
        assert bl.size == 2

        removed = bl.cleanup()
        assert removed == 1
        assert bl.is_revoked("expired_jti") is False
        assert bl.is_revoked("active_jti") is True

    def test_size(self) -> None:
        bl = TokenBlacklist()
        assert bl.size == 0
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        bl.revoke("a", exp)
        bl.revoke("b", exp)
        assert bl.size == 2
