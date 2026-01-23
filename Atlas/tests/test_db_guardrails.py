"""Guardrail tests for OracleConnector query limits and timeouts."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.connectors.oracle.connector import OracleConnector, QueryGuardrailError


def _build_mock_pool(
    columns: list[str],
    rows: list[tuple],
    execute_delay: float = 0.0,
) -> MagicMock:
    """
    Build a mocked async connection pool that yields a fake connection/cursor.

    Args:
        columns: Column names for cursor.description
        rows: Row tuples to return from fetchmany
        execute_delay: Optional delay in seconds for cursor.execute

    Returns:
        MagicMock configured to behave like an async connection pool
    """
    cursor = AsyncMock()
    cursor.description = [(column,) for column in columns]
    if execute_delay:
        async def _delayed_execute(*_args, **_kwargs) -> None:
            await asyncio.sleep(execute_delay)

        cursor.execute = AsyncMock(side_effect=_delayed_execute)
    else:
        cursor.execute = AsyncMock()
    cursor.fetchmany = AsyncMock(return_value=rows)

    cursor_context = AsyncMock()
    cursor_context.__aenter__.return_value = cursor
    cursor_context.__aexit__.return_value = None

    connection = MagicMock()
    connection.cursor.return_value = cursor_context

    connection_context = AsyncMock()
    connection_context.__aenter__.return_value = connection
    connection_context.__aexit__.return_value = None

    pool = MagicMock()
    pool.acquire.return_value = connection_context
    return pool


@pytest.fixture
def connector() -> OracleConnector:
    """Create an OracleConnector instance with oracledb mocked."""
    with patch("atlas.connectors.oracle.connector.oracledb.init_oracle_client"):
        return OracleConnector(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/ORCL",
        )


@pytest.mark.asyncio
async def test_timeout_guardrail_triggers(connector: OracleConnector) -> None:
    """Timeout guardrail should raise a QueryGuardrailError."""
    connector._timeout_seconds = 0.01
    connector._max_rows = 1000
    connector._pool = _build_mock_pool(
        columns=["ID"],
        rows=[(1,)],
        execute_delay=0.05,
    )

    with pytest.raises(QueryGuardrailError) as exc_info:
        await connector.execute_query("SELECT ID FROM USERS")

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_row_limit_guardrail_triggers(connector: OracleConnector) -> None:
    """Row limit guardrail should raise a QueryGuardrailError."""
    connector._timeout_seconds = 30.0
    connector._max_rows = 2
    connector._pool = _build_mock_pool(
        columns=["ID"],
        rows=[(1,), (2,), (3,)],
    )

    with pytest.raises(QueryGuardrailError) as exc_info:
        await connector.execute_query("SELECT ID FROM USERS")

    assert "maximum allowed rows" in str(exc_info.value).lower()
