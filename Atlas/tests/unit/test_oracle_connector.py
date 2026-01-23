"""Unit tests for Oracle Connector Lite."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.connectors.oracle.connector import (
    ColumnInfo,
    OracleConnector,
    ReadOnlyViolationError,
)


class TestValidateQuery:
    """Tests for the validate_query security method."""

    @pytest.fixture
    def connector(self) -> OracleConnector:
        """Create an OracleConnector instance with oracledb mocked."""
        with patch("atlas.connectors.oracle.connector.oracledb.init_oracle_client"):
            return OracleConnector(
                user="test_user",
                password="test_pass",
                dsn="localhost:1521/ORCL",
            )

    def test_allows_select_queries(self, connector: OracleConnector) -> None:
        """SELECT queries should be allowed."""
        valid_queries = [
            "SELECT * FROM employees",
            "SELECT id, name FROM users WHERE active = 1",
            "SELECT COUNT(*) FROM orders",
            "select lower(name) from products",
        ]
        for sql in valid_queries:
            connector.validate_query(sql)  # Should not raise

    def test_blocks_insert(self, connector: OracleConnector) -> None:
        """INSERT queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("INSERT INTO users VALUES (1, 'test')")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_update(self, connector: OracleConnector) -> None:
        """UPDATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("UPDATE users SET name = 'test' WHERE id = 1")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_delete(self, connector: OracleConnector) -> None:
        """DELETE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("DELETE FROM users WHERE id = 1")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_drop(self, connector: OracleConnector) -> None:
        """DROP queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("DROP TABLE users")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_alter(self, connector: OracleConnector) -> None:
        """ALTER queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("ALTER TABLE users ADD COLUMN age INT")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_truncate(self, connector: OracleConnector) -> None:
        """TRUNCATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("TRUNCATE TABLE users")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_blocks_create(self, connector: OracleConnector) -> None:
        """CREATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("CREATE TABLE new_table (id INT)")
        assert "Only SELECT queries are allowed" in str(exc_info.value)

    def test_case_insensitive_detection(self, connector: OracleConnector) -> None:
        """Forbidden operations should be detected regardless of case."""
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("insert into users values (1)")
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("INSERT INTO users VALUES (1)")
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("Insert Into users Values (1)")

    def test_allows_keywords_in_strings(self, connector: OracleConnector) -> None:
        """Keywords inside string literals should be allowed."""
        sql = "SELECT * FROM logs WHERE action = 'DELETE'"
        connector.validate_query(sql)

    def test_blocks_multiple_statements(self, connector: OracleConnector) -> None:
        """Multiple SQL statements should be blocked."""
        sql = "SELECT * FROM users; SELECT * FROM orders"
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query(sql)

    def test_blocks_union_queries(self, connector: OracleConnector) -> None:
        """UNION queries should be blocked per strict SELECT/WITH policy."""
        sql = "SELECT id FROM users UNION SELECT id FROM admins"
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query(sql)

    def test_allows_with_queries(self, connector: OracleConnector) -> None:
        """WITH queries should be allowed when read-only."""
        sql = "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent"
        connector.validate_query(sql)


class TestExecuteQuery:
    """Tests for execute_query with a fully mocked connection pool."""

    @staticmethod
    def _build_mock_pool(columns: list[str], rows: list[tuple]) -> AsyncMock:
        """
        Build a mocked async connection pool that yields a fake connection/cursor.

        Args:
            columns: Column names for cursor.description
            rows: Row tuples to return from fetchall

        Returns:
            AsyncMock configured to behave like an async connection pool
        """
        cursor = AsyncMock()
        cursor.description = [(column,) for column in columns]
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
    def connector(self) -> OracleConnector:
        """Create an OracleConnector instance with oracledb mocked."""
        with patch("atlas.connectors.oracle.connector.oracledb.init_oracle_client"):
            return OracleConnector(
                user="test_user",
                password="test_pass",
                dsn="localhost:1521/ORCL",
            )

    @pytest.mark.asyncio
    async def test_execute_query_returns_rows(self, connector: OracleConnector) -> None:
        """execute_query should return rows as dictionaries."""
        connector._pool = self._build_mock_pool(
            columns=["ID", "NAME"],
            rows=[(1, "Alice"), (2, "Bob")],
        )

        results = await connector.execute_query("SELECT ID, NAME FROM USERS")

        assert results == [{"ID": 1, "NAME": "Alice"}, {"ID": 2, "NAME": "Bob"}]

    @pytest.mark.asyncio
    async def test_execute_query_raises_if_not_connected(self, connector: OracleConnector) -> None:
        """execute_query should raise if the pool is not initialized."""
        connector._pool = None

        with pytest.raises(RuntimeError):
            await connector.execute_query("SELECT * FROM USERS")

    @pytest.mark.asyncio
    async def test_execute_query_blocks_invalid_sql(self, connector: OracleConnector) -> None:
        """execute_query should enforce the AST validator before execution."""
        connector._pool = self._build_mock_pool(columns=["ID"], rows=[(1,)])

        with pytest.raises(ReadOnlyViolationError):
            await connector.execute_query("DELETE FROM USERS WHERE ID = 1")


class TestColumnInfo:
    """Tests for the ColumnInfo dataclass."""

    def test_column_info_creation(self) -> None:
        """ColumnInfo should store column metadata correctly."""
        col = ColumnInfo(
            name="EMPLOYEE_ID",
            data_type="NUMBER",
            nullable=False,
            data_length=22,
        )
        assert col.name == "EMPLOYEE_ID"
        assert col.data_type == "NUMBER"
        assert col.nullable is False
        assert col.data_length == 22

    def test_column_info_defaults(self) -> None:
        """ColumnInfo should have sensible defaults."""
        col = ColumnInfo(
            name="STATUS",
            data_type="VARCHAR2",
            nullable=True,
        )
        assert col.data_length is None
