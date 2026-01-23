"""SQL security tests for the OracleConnector validator."""

import pytest

from atlas.connectors.oracle.connector import OracleConnector, ReadOnlyViolationError


@pytest.fixture
def connector() -> OracleConnector:
    """
    Create an OracleConnector instance without initializing the Oracle client.

    The SQL validator is self-contained and does not depend on a live database
    connection, so we bypass __init__ to avoid requiring Oracle client libraries.
    """
    return OracleConnector.__new__(OracleConnector)


def test_allows_select_and_with(connector: OracleConnector) -> None:
    """SELECT and WITH statements should be allowed."""
    connector.validate_query("SELECT * FROM employees")
    connector.validate_query("WITH recent AS (SELECT * FROM orders) SELECT * FROM recent")


def test_rejects_ddl_and_dml(connector: OracleConnector) -> None:
    """DDL/DML statements must be rejected."""
    with pytest.raises(ReadOnlyViolationError):
        connector.validate_query("DELETE FROM users WHERE id = 1")
    with pytest.raises(ReadOnlyViolationError):
        connector.validate_query("CREATE TABLE audit_log (id INT)")


def test_rejects_multi_statement_queries(connector: OracleConnector) -> None:
    """Query batching should be rejected to prevent injection."""
    with pytest.raises(ReadOnlyViolationError):
        connector.validate_query("SELECT * FROM users; SELECT * FROM orders")


def test_rejects_mixed_statements(connector: OracleConnector) -> None:
    """Mixed statement batches should be rejected."""
    with pytest.raises(ReadOnlyViolationError):
        connector.validate_query("SELECT * FROM users; DROP TABLE users")
