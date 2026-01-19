"""Unit tests for Oracle Connector Lite."""

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
        """Create an OracleConnector instance for testing."""
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
        assert "INSERT" in str(exc_info.value)

    def test_blocks_update(self, connector: OracleConnector) -> None:
        """UPDATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("UPDATE users SET name = 'test' WHERE id = 1")
        assert "UPDATE" in str(exc_info.value)

    def test_blocks_delete(self, connector: OracleConnector) -> None:
        """DELETE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("DELETE FROM users WHERE id = 1")
        assert "DELETE" in str(exc_info.value)

    def test_blocks_drop(self, connector: OracleConnector) -> None:
        """DROP queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("DROP TABLE users")
        assert "DROP" in str(exc_info.value)

    def test_blocks_alter(self, connector: OracleConnector) -> None:
        """ALTER queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("ALTER TABLE users ADD COLUMN age INT")
        assert "ALTER" in str(exc_info.value)

    def test_blocks_truncate(self, connector: OracleConnector) -> None:
        """TRUNCATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("TRUNCATE TABLE users")
        assert "TRUNCATE" in str(exc_info.value)

    def test_blocks_create(self, connector: OracleConnector) -> None:
        """CREATE queries should be blocked."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            connector.validate_query("CREATE TABLE new_table (id INT)")
        assert "CREATE" in str(exc_info.value)

    def test_case_insensitive_detection(self, connector: OracleConnector) -> None:
        """Forbidden keywords should be detected regardless of case."""
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("insert into users values (1)")
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("INSERT INTO users VALUES (1)")
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query("Insert Into users Values (1)")

    def test_allows_keywords_in_strings(self, connector: OracleConnector) -> None:
        """Keywords inside string literals should ideally not trigger blocking.

        Note: This is a known limitation - the current regex-based approach
        cannot distinguish between keywords in SQL context vs string literals.
        This test documents the expected behavior for a more sophisticated parser.
        """
        # This query contains 'DELETE' as a column value, not a SQL command
        # A more sophisticated parser would allow this
        sql = "SELECT * FROM logs WHERE action = 'DELETE'"
        # Current implementation will block this - documenting as expected behavior
        with pytest.raises(ReadOnlyViolationError):
            connector.validate_query(sql)


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
