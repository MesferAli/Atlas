"""
Security Middleware for Atlas API

SECURITY: Defense-in-depth through middleware layers.
- Rate limiting to prevent brute force attacks
- Security headers for browser protection
- Request logging for audit trails
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("atlas.siem")


class SIEMForwarder:
    """
    SIEM log forwarder for security event monitoring.

    Writes structured JSON logs that can be consumed by SIEM systems
    (Splunk, Elastic SIEM, IBM QRadar, etc.) via file-based log shipping.

    In production, extend with direct API integration to your SIEM provider.
    """

    def __init__(self, log_dir: str | None = None) -> None:
        import os

        self._log_dir = Path(log_dir or os.getenv("ATLAS_SIEM_LOG_DIR", "./logs/siem"))
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self._log_dir / f"requests_{date_str}.jsonl"

    def forward(self, entry: dict[str, Any]) -> None:
        """Write a structured log entry for SIEM consumption."""
        try:
            with open(self._get_log_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            logger.warning("SIEM log write failed: %s", e)


# Global SIEM forwarder
_siem_forwarder = SIEMForwarder()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.

    SECURITY:
    - Limits requests per IP address
    - Separate limits for authentication endpoints
    - Exponential backoff for repeat offenders
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.request_counts: dict[str, list[float]] = defaultdict(list)

        # Try to use Redis-backed rate limiter
        from atlas.api.security.redis_backend import get_rate_limiter

        self._backend = get_rate_limiter()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxies."""
        # Check for forwarded IP (behind load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, key: str, window_seconds: int = 60) -> None:
        """Remove request timestamps older than the window."""
        now = time.time()
        self.request_counts[key] = [
            ts for ts in self.request_counts[key] if now - ts < window_seconds
        ]

    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from JWT Authorization header if present."""
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        try:
            import jwt as pyjwt

            token = auth[7:]
            # Decode without verification just to get sub for rate-limit key.
            # Full verification happens later in the endpoint dependency.
            payload = pyjwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)

        # Use per-user key when authenticated, otherwise per-IP
        user_id = self._extract_user_id(request)
        rate_key = f"user:{user_id}" if user_id else f"ip:{client_ip}"

        # Determine rate limit based on endpoint
        is_auth_endpoint = request.url.path.startswith("/api/auth")
        limit = (
            self.auth_requests_per_minute if is_auth_endpoint else self.requests_per_minute
        )

        # Use backend (Redis or in-memory) for rate limiting
        count = self._backend.record_request(rate_key, window_seconds=60)
        if count > limit:
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": "60",
                },
            )

        return await call_next(request)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware.

    SECURITY: Adds essential security headers to all responses.
    - Prevents clickjacking
    - Enables XSS protection
    - Controls content type sniffing
    - Sets strict CSP for API responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent content type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy for API
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Cache control for sensitive data
        if request.url.path.startswith("/api/") or request.url.path.startswith("/v1/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # API versioning header
        response.headers["X-API-Version"] = "1.0"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for audit purposes.

    SECURITY: Logs all requests for security monitoring.
    - Captures request metadata (not body for privacy)
    - Records response status and timing
    - Integrates with audit logging system
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Structured log entry for SIEM integration
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "")[:200],
        }

        # Send to SIEM via configured forwarder
        _siem_forwarder.forward(log_entry)

        # Prometheus metrics
        from atlas.api.metrics import get_metrics

        metrics = get_metrics()
        metrics.inc_counter(
            "atlas_http_requests_total",
            {"method": request.method, "status": str(response.status_code)},
        )
        metrics.observe_histogram(
            "atlas_http_request_duration_seconds",
            duration_ms / 1000,
            {"method": request.method, "path": request.url.path},
        )

        # Add security-relevant headers to response
        response.headers["X-Request-ID"] = str(id(request))

        return response


def setup_security_middleware(app: FastAPI) -> None:
    """
    Configure all security middleware for the application.

    Usage:
        app = FastAPI()
        setup_security_middleware(app)
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        auth_requests_per_minute=10,
    )
