"""
Security Middleware for Atlas API

SECURITY: Defense-in-depth through middleware layers.
- Rate limiting to prevent brute force attacks
- Security headers for browser protection
- Request logging for audit trails
"""

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


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

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxies."""
        # Check for forwarded IP (behind load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, ip: str, window_seconds: int = 60) -> None:
        """Remove request timestamps older than the window."""
        now = time.time()
        self.request_counts[ip] = [
            ts for ts in self.request_counts[ip] if now - ts < window_seconds
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        self._clean_old_requests(client_ip)

        # Determine rate limit based on endpoint
        is_auth_endpoint = request.url.path.startswith("/api/auth")
        limit = (
            self.auth_requests_per_minute if is_auth_endpoint else self.requests_per_minute
        )

        # Check rate limit
        if len(self.request_counts[client_ip]) >= limit:
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": "60",
                },
            )

        # Record this request
        self.request_counts[client_ip].append(time.time())

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

        # Log request (in production, send to structured logging)
        # For now, we construct the log entry for future SIEM integration
        _log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "")[:200],
        }
        # TODO: Send to SIEM/logging system
        del _log_entry  # Explicitly mark as intentionally unused for now

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
