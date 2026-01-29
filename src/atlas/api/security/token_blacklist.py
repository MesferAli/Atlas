"""
Token Blacklist for JWT Revocation

SECURITY: Provides token revocation support via an in-memory blacklist
with TTL-based expiration. In production, replace with Redis or PostgreSQL.
"""

import threading
import time
from datetime import datetime


class TokenBlacklist:
    """
    In-memory token blacklist with automatic expiration cleanup.

    SECURITY:
    - Tokens are identified by their JTI (JWT ID)
    - Expired entries are automatically pruned
    - Thread-safe for concurrent access

    In production, use Redis with TTL keys for distributed revocation:
        redis.setex(f"blacklist:{jti}", ttl_seconds, "1")
    """

    def __init__(self) -> None:
        self._blacklist: dict[str, float] = {}  # jti -> expiration timestamp
        self._lock = threading.Lock()

    def revoke(self, jti: str, expires_at: datetime) -> None:
        """
        Add a token to the blacklist.

        Args:
            jti: The unique token identifier
            expires_at: When the token expires (used for cleanup)
        """
        with self._lock:
            self._blacklist[jti] = expires_at.timestamp()

    def is_revoked(self, jti: str) -> bool:
        """
        Check if a token has been revoked.

        Args:
            jti: The unique token identifier

        Returns:
            True if the token is blacklisted
        """
        with self._lock:
            return jti in self._blacklist

    def cleanup(self) -> int:
        """
        Remove expired entries from the blacklist.

        Returns:
            Number of entries removed
        """
        now = time.time()
        with self._lock:
            expired = [jti for jti, exp in self._blacklist.items() if exp < now]
            for jti in expired:
                del self._blacklist[jti]
            return len(expired)

    @property
    def size(self) -> int:
        """Number of tokens currently blacklisted."""
        with self._lock:
            return len(self._blacklist)


# Global singleton
_token_blacklist: TokenBlacklist | None = None


def get_token_blacklist() -> TokenBlacklist:
    """Get or create the global token blacklist."""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist
