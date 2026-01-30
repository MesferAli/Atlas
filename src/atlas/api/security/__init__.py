"""
Atlas Security Module

SECURITY ARCHITECTURE - BACKEND ENFORCEMENT:
- All data access MUST go through authenticated server-side endpoints
- Row Level Security (RLS) policies are enforced at the database layer
- Input validation is performed using Pydantic models with strict constraints
- Audit logging captures all sensitive operations

This module implements the Security & Architecture Manifesto requirements.
"""

from atlas.api.security.audit import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
)
from atlas.api.security.auth import (
    create_access_token,
    get_current_user,
    get_current_user_optional,
    get_password_hash,
    require_auth,
    verify_password,
    verify_token,
)
from atlas.api.security.middleware import (
    RateLimitMiddleware,
    SecurityMiddleware,
)
from atlas.api.security.models import (
    AuthRequest,
    AuthResponse,
    RegisterRequest,
    TokenPayload,
    UserProfile,
    validate_input,
)

__all__ = [
    # Models
    "AuthRequest",
    "AuthResponse",
    "RegisterRequest",
    "TokenPayload",
    "UserProfile",
    "validate_input",
    # Auth
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_current_user_optional",
    "get_password_hash",
    "verify_password",
    "require_auth",
    # Middleware
    "SecurityMiddleware",
    "RateLimitMiddleware",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
]
