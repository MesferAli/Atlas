"""Atlas API package - FastAPI application for DB guardrails."""

from atlas.api.main import app
from atlas.api.safe_db_connector import execute_protected_query

__all__ = ["app", "execute_protected_query"]
