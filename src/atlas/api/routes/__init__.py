"""Atlas API Routes."""

from atlas.api.routes.audit import router as audit_router
from atlas.api.routes.auth import router as auth_router

__all__ = ["auth_router", "audit_router"]
