"""Safe DB Connector - Protected SQL execution wrapper for the API layer.

This module provides a high-level interface for executing SQL queries
through the OracleConnector with full guardrail protection.
"""

from __future__ import annotations

import os
from typing import Any

from atlas.connectors.oracle.connector import (
    OracleConnector,
    QueryGuardrailError,
    ReadOnlyViolationError,
)

# Configuration from environment with sensible defaults
DB_USER = os.getenv("ATLAS_DB_USER", "")
DB_PASSWORD = os.getenv("ATLAS_DB_PASSWORD", "")
DB_DSN = os.getenv("ATLAS_DB_DSN", "")
DB_TIMEOUT = int(os.getenv("ATLAS_DB_TIMEOUT_SECONDS", "30"))
DB_MAX_ROWS = int(os.getenv("ATLAS_DB_MAX_ROWS", "1000"))

# Global connector instance (lazy initialization)
_connector: OracleConnector | None = None


def _get_connector() -> OracleConnector:
    """Get or create the global OracleConnector instance.

    Returns:
        Configured OracleConnector with guardrails.

    Raises:
        RuntimeError: If database credentials are not configured.
    """
    global _connector

    if _connector is None:
        if not all([DB_USER, DB_PASSWORD, DB_DSN]):
            raise RuntimeError(
                "Database credentials not configured. "
                "Set ATLAS_DB_USER, ATLAS_DB_PASSWORD, and ATLAS_DB_DSN."
            )

        _connector = OracleConnector(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            timeout_seconds=DB_TIMEOUT,
            max_rows=DB_MAX_ROWS,
        )

    return _connector


async def execute_protected_query(sql: str) -> dict[str, Any]:
    """Execute a SQL query with full guardrail protection.

    This function validates the query and executes it through the
    OracleConnector, catching and translating all guardrail exceptions
    into user-friendly error responses.

    Args:
        sql: The SQL query to execute.

    Returns:
        Dictionary with 'status' key and either 'data' or 'error' key.
        - On success: {"status": "success", "data": [...]}
        - On failure: {"status": "error", "error": "..."}
    """
    try:
        connector = _get_connector()

        # Ensure connection is established
        if connector._pool is None:
            await connector.connect()

        # Execute with guardrails
        results = await connector.execute_query(sql)

        return {
            "status": "success",
            "data": results,
        }

    except ReadOnlyViolationError as e:
        return {
            "status": "error",
            "error": f"Security violation: {e}",
        }

    except QueryGuardrailError as e:
        return {
            "status": "error",
            "error": f"Query limit exceeded: {e}",
        }

    except RuntimeError as e:
        return {
            "status": "error",
            "error": str(e),
        }

    except Exception as e:
        # Log unexpected errors but don't expose internals
        print(f"[ERROR] Unexpected database error: {e}")
        return {
            "status": "error",
            "error": "An internal error occurred. Please try again later.",
        }
