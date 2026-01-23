"""Concurrency guardrail tests for OracleConnector."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.connectors.oracle.connector import OracleConnector, QueryGuardrailError


def _build_pool_factory(
    columns: list[str],
    rows: list[tuple],
    execute_delay: float,
) -> MagicMock:
    """
    Build a mocked async connection pool that yields new connection/cursor contexts.

    Args:
        columns: Column names for cursor.description
        rows: Row tuples to return from fetchmany
        execute_delay: Delay to simulate a slow query execution

    Returns:
        MagicMock configured to behave like an async connection pool
    """
    def _build_context() -> AsyncMock:
        cursor = AsyncMock()
        cursor.description = [(column,) for column in columns]

        async def _delayed_execute(*_args, **_kwargs) -> None:
            await asyncio.sleep(execute_delay)

        cursor.execute = AsyncMock(side_effect=_delayed_execute)
        cursor.fetchmany = AsyncMock(return_value=rows)

        cursor_context = AsyncMock()
        cursor_context.__aenter__.return_value = cursor
        cursor_context.__aexit__.return_value = None

        connection = MagicMock()
        connection.cursor.return_value = cursor_context

        connection_context = AsyncMock()
        connection_context.__aenter__.return_value = connection
        connection_context.__aexit__.return_value = None
        return connection_context

    pool = MagicMock()
    pool.acquire.side_effect = _build_context
    return pool


@pytest.fixture
def connector() -> OracleConnector:
    """Create an OracleConnector instance with oracledb mocked."""
    with patch("atlas.connectors.oracle.connector.oracledb.init_oracle_client"):
        return OracleConnector(
            user="test_user",
            password="test_pass",
            dsn="localhost:1521/ORCL",
            timeout_seconds=0.05,
            max_rows=100,
        )


@pytest.mark.asyncio
async def test_high_concurrency_guardrails(connector: OracleConnector) -> None:
    """
    Validate guardrails under concurrent load.

    Ensures that at least one timeout guardrail triggers when running many
    concurrent queries against a slow mocked execution path.
    """
    connector._pool = _build_pool_factory(
        columns=["ID"],
        rows=[(1,)],
        execute_delay=0.2,
    )

    tasks = [connector.execute_query("SELECT * FROM heavy_table") for _ in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    guardrail_errors = [result for result in results if isinstance(result, QueryGuardrailError)]
    assert len(guardrail_errors) > 0
