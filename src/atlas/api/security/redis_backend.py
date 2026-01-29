"""
Redis Backend for Atlas API

Provides Redis-backed rate limiting and token blacklist that survive restarts.
Falls back to in-memory implementation when Redis is unavailable.

SECURITY: Token blacklist entries use Redis TTL to auto-expire with the JWT.
"""

import logging
import os
import time
from datetime import datetime
from typing import Protocol

logger = logging.getLogger("atlas.redis")


class RateLimiterBackend(Protocol):
    """Protocol for rate limiter backends."""

    def record_request(self, key: str, window_seconds: int) -> int:
        """Record a request and return the count within the window."""
        ...

    def clear(self) -> None:
        """Clear all rate limit data."""
        ...


class TokenBlacklistBackend(Protocol):
    """Protocol for token blacklist backends."""

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        """Revoke a token with a TTL."""
        ...

    def is_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        ...


# ── Redis implementations ────────────────────────────────────────────


class RedisRateLimiter:
    """Redis-backed sliding window rate limiter."""

    def __init__(self, redis_client: "Redis") -> None:  # type: ignore[name-defined]
        self._r = redis_client

    def record_request(self, key: str, window_seconds: int = 60) -> int:
        now = time.time()
        redis_key = f"ratelimit:{key}"
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
        pipe.zadd(redis_key, {str(now): now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds + 1)
        results = pipe.execute()
        return results[2]  # zcard result

    def clear(self) -> None:
        for key in self._r.scan_iter("ratelimit:*"):
            self._r.delete(key)


class RedisTokenBlacklist:
    """Redis-backed token blacklist with TTL auto-expiry."""

    def __init__(self, redis_client: "Redis") -> None:  # type: ignore[name-defined]
        self._r = redis_client

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        self._r.setex(f"blacklist:{jti}", ttl_seconds, "1")

    def is_revoked(self, jti: str) -> bool:
        return self._r.exists(f"blacklist:{jti}") > 0


# ── In-memory fallbacks ──────────────────────────────────────────────


class InMemoryRateLimiter:
    """In-memory sliding window rate limiter (single-process only)."""

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}

    def record_request(self, key: str, window_seconds: int = 60) -> int:
        now = time.time()
        if key not in self._windows:
            self._windows[key] = []
        self._windows[key] = [
            ts for ts in self._windows[key] if now - ts < window_seconds
        ]
        self._windows[key].append(now)
        return len(self._windows[key])

    def clear(self) -> None:
        self._windows.clear()


class InMemoryTokenBlacklist:
    """In-memory token blacklist (single-process only)."""

    def __init__(self) -> None:
        self._store: dict[str, float] = {}  # jti -> expire_timestamp

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        self._store[jti] = time.time() + ttl_seconds

    def is_revoked(self, jti: str) -> bool:
        exp = self._store.get(jti)
        if exp is None:
            return False
        if time.time() > exp:
            del self._store[jti]
            return False
        return True


# ── Factory ───────────────────────────────────────────────────────────

_rate_limiter: RateLimiterBackend | None = None
_token_bl: TokenBlacklistBackend | None = None


def _connect_redis():
    """Attempt Redis connection, return client or None."""
    redis_url = os.getenv("ATLAS_REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis

        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
        client.ping()
        logger.info("Connected to Redis at %s", redis_url)
        return client
    except Exception as e:
        logger.warning("Redis unavailable (%s), using in-memory fallback", e)
        return None


def get_rate_limiter() -> RateLimiterBackend:
    """Get or create the rate limiter backend."""
    global _rate_limiter
    if _rate_limiter is None:
        client = _connect_redis()
        if client:
            _rate_limiter = RedisRateLimiter(client)
        else:
            _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def get_token_blacklist_backend() -> TokenBlacklistBackend:
    """Get or create the token blacklist backend."""
    global _token_bl
    if _token_bl is None:
        client = _connect_redis()
        if client:
            _token_bl = RedisTokenBlacklist(client)
        else:
            _token_bl = InMemoryTokenBlacklist()
    return _token_bl
