"""Oracle Connector Lite - Read-only Oracle database connector using python-oracledb Thin Mode."""

import re
from dataclasses import dataclass
from typing import Any

import oracledb


class ReadOnlyViolationError(Exception):
    """Raised when a query attempts to modify data."""

    pass


@dataclass
class ColumnInfo:
    """Schema information for a database column."""

    name: str
    data_type: str
    nullable: bool
    data_length: int | None = None


class OracleConnector:
    """
    Read-only Oracle database connector using python-oracledb Thin Mode.

    This connector enforces read-only access to Oracle databases and does not
    require Oracle Instant Client installation.
    """

    # SQL keywords that indicate data modification (DDL/DML)
    FORBIDDEN_KEYWORDS = frozenset(
        {
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "MERGE",
            "GRANT",
            "REVOKE",
        }
    )

    # Pattern to match forbidden keywords as whole words
    _KEYWORD_PATTERN = re.compile(
        r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        user: str,
        password: str,
        dsn: str,
    ) -> None:
        """
        Initialize the Oracle connector.

        Args:
            user: Database username
            password: Database password
            dsn: Data Source Name (host:port/service_name)
        """
        # Uses Thin Mode by default - no Oracle Client required
        # Do NOT call init_oracle_client() to stay in thin mode
        self._user = user
        self._password = password
        self._dsn = dsn
        self._pool: oracledb.AsyncConnectionPool | None = None

    async def connect(self) -> None:
        """Establish an async connection pool to the Oracle database."""
        self._pool = oracledb.create_pool_async(
            user=self._user,
            password=self._password,
            dsn=self._dsn,
            min=1,
            max=5,
        )

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    def validate_query(self, sql: str) -> None:
        """
        Validate that a SQL query is read-only.

        Args:
            sql: The SQL query to validate

        Raises:
            ReadOnlyViolationError: If the query contains forbidden keywords
        """
        match = self._KEYWORD_PATTERN.search(sql)
        if match:
            keyword = match.group(1).upper()
            raise ReadOnlyViolationError(
                f"Query contains forbidden keyword: {keyword}. Only SELECT queries are allowed."
            )

    async def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a read-only SQL query.

        Args:
            sql: The SQL query to execute (must be SELECT)
            params: Optional query parameters

        Returns:
            List of rows as dictionaries

        Raises:
            ReadOnlyViolationError: If the query is not read-only
            RuntimeError: If not connected
        """
        self.validate_query(sql)

        if not self._pool:
            raise RuntimeError("Not connected. Call connect() first.")

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, params or {})
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    async def get_table_schema(self, table_name: str) -> list[ColumnInfo]:
        """
        Get schema information for a table by querying ALL_TAB_COLUMNS.

        Args:
            table_name: Name of the table (case-insensitive)

        Returns:
            List of ColumnInfo objects describing the table columns
        """
        sql = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                NULLABLE,
                DATA_LENGTH
            FROM ALL_TAB_COLUMNS
            WHERE UPPER(TABLE_NAME) = UPPER(:table_name)
            ORDER BY COLUMN_ID
        """

        rows = await self.execute_query(sql, {"table_name": table_name})

        return [
            ColumnInfo(
                name=row["COLUMN_NAME"],
                data_type=row["DATA_TYPE"],
                nullable=row["NULLABLE"] == "Y",
                data_length=row["DATA_LENGTH"],
            )
            for row in rows
        ]

    async def __aenter__(self) -> "OracleConnector":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
