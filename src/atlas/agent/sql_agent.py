"""Oracle SQL RAG Agent - Natural language to SQL query execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from atlas.connectors.oracle.connector import OracleConnector, ReadOnlyViolationError
from atlas.connectors.oracle.indexer import OracleSchemaIndexer


@dataclass
class AgentResponse:
    """Response from the SQL agent."""

    question: str
    relevant_tables: list[dict[str, Any]]
    generated_sql: str
    results: list[dict[str, Any]] | None
    error: str | None = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        pass


class MockLLM(BaseLLM):
    """Mock LLM for MVP testing - returns predefined SQL based on keywords."""

    async def generate(self, prompt: str) -> str:
        """Generate mock SQL based on question keywords (supports Arabic)."""
        prompt_lower = prompt.lower()

        # Arabic keyword patterns
        # رواتب = salaries, إجمالي = total, الشهر الماضي = last month
        # موظفين = employees, عملاء = customers

        # Salary/Payroll queries (Arabic: رواتب، إجمالي)
        is_salary_query = (
            "رواتب" in prompt
            or "إجمالي" in prompt
            or ("salary" in prompt_lower and "total" in prompt_lower)
        )
        if is_salary_query:
            return """SELECT
    SUM(SALARY_AMOUNT) AS TOTAL_SALARIES,
    TO_CHAR(PAYMENT_DATE, 'YYYY-MM') AS PAYMENT_MONTH
FROM HR.PAYROLL
WHERE PAYMENT_DATE >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -1)
  AND PAYMENT_DATE < TRUNC(SYSDATE, 'MM')
GROUP BY TO_CHAR(PAYMENT_DATE, 'YYYY-MM')"""

        # Customer queries
        elif "top" in prompt_lower and "customer" in prompt_lower:
            return "SELECT * FROM CUSTOMERS ORDER BY TOTAL_PURCHASES DESC FETCH FIRST 5 ROWS ONLY"

        # Employee/Salary queries
        elif "employee" in prompt_lower and "salary" in prompt_lower:
            return "SELECT EMPLOYEE_NAME, SALARY FROM EMPLOYEES ORDER BY SALARY DESC"

        # Order queries
        elif "order" in prompt_lower and "recent" in prompt_lower:
            return "SELECT * FROM ORDERS ORDER BY ORDER_DATE DESC FETCH FIRST 10 ROWS ONLY"

        # Count queries
        elif "count" in prompt_lower or "عدد" in prompt:
            return "SELECT COUNT(*) AS TOTAL FROM CUSTOMERS"

        else:
            # Default: simple select from first mentioned table
            return "SELECT * FROM DUAL"


class OracleSQLAgent:
    """
    SQL RAG Agent that converts natural language questions to Oracle SQL queries.

    This agent:
    1. Uses semantic search to find relevant tables
    2. Constructs a prompt with schema context
    3. Generates SQL via LLM
    4. Validates the SQL is read-only
    5. Executes and returns results
    """

    # Bilingual system prompt (Arabic/English)
    SYSTEM_PROMPT = (
        "أنت خبير في Oracle SQL. مهمتك كتابة استعلام SQL.\n"
        "You are an Oracle SQL Expert. Write a SQL query.\n\n"
        "القواعد / Rules:\n"
        "- اكتب فقط استعلامات SELECT\n"
        "- Write ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)\n"
        "- Use proper Oracle SQL syntax\n"
        "- Return only the SQL query, no explanations\n\n"
        "الجداول المتاحة / Available Tables:\n"
        "{schema_context}\n\n"
        "سؤال المستخدم / User Question: {question}\n\n"
        "SQL Query:"
    )

    def __init__(
        self,
        connector: OracleConnector,
        indexer: OracleSchemaIndexer,
        llm: BaseLLM | None = None,
    ) -> None:
        """
        Initialize the SQL RAG Agent.

        Args:
            connector: OracleConnector for executing queries
            indexer: OracleSchemaIndexer for semantic table search
            llm: LLM provider for SQL generation (defaults to MockLLM)
        """
        self._connector = connector
        self._indexer = indexer
        self._llm = llm or MockLLM()

    def _build_schema_context(self, tables: list[dict[str, Any]]) -> str:
        """Build schema context string from table metadata."""
        if not tables:
            return "No relevant tables found."

        lines = []
        for table in tables:
            table_desc = f"- {table['owner']}.{table['table_name']}"
            if table.get("comments"):
                table_desc += f": {table['comments']}"
            lines.append(table_desc)

        return "\n".join(lines)

    def _build_prompt(self, question: str, tables: list[dict[str, Any]]) -> str:
        """Build the LLM prompt with schema context."""
        schema_context = self._build_schema_context(tables)
        return self.SYSTEM_PROMPT.format(
            schema_context=schema_context,
            question=question,
        )

    async def run(
        self,
        question: str,
        table_limit: int = 5,
        user_role: str | None = None,
    ) -> AgentResponse:
        """
        Process a natural language question and return SQL results.

        Args:
            question: Natural language question (e.g., "Show me top 5 customers")
            table_limit: Maximum number of relevant tables to consider
            user_role: User's RBAC role for Data Moat filtering

        Returns:
            AgentResponse with generated SQL and query results
        """
        # Step 1: Find relevant tables using semantic search
        relevant_tables = self._indexer.search_tables(question, limit=table_limit)

        # Step 1.5: Apply Data Moat role-based filtering
        # SECURITY: Always filter. When user_role is None (unauthenticated),
        # default to "viewer" — the most restrictive named role. This ensures
        # SECRET tables are never leaked to anonymous or unauthenticated users.
        if relevant_tables:
            from atlas.connectors.oracle.data_moat import filter_tables_by_role

            effective_role = user_role or "viewer"
            relevant_tables = filter_tables_by_role(
                relevant_tables, effective_role
            )

        # Step 2: Build prompt with schema context
        prompt = self._build_prompt(question, relevant_tables)

        # Step 3: Generate SQL via LLM
        generated_sql = await self._llm.generate(prompt)
        generated_sql = generated_sql.strip()

        # Step 4: Validate the generated SQL is read-only
        try:
            self._connector.validate_query(generated_sql)
        except ReadOnlyViolationError as e:
            return AgentResponse(
                question=question,
                relevant_tables=relevant_tables,
                generated_sql=generated_sql,
                results=None,
                error=f"Generated SQL violates read-only policy: {e}",
            )

        # Step 5: Execute the query
        try:
            results = await self._connector.execute_query(generated_sql)
            return AgentResponse(
                question=question,
                relevant_tables=relevant_tables,
                generated_sql=generated_sql,
                results=results,
            )
        except Exception as e:
            return AgentResponse(
                question=question,
                relevant_tables=relevant_tables,
                generated_sql=generated_sql,
                results=None,
                error=f"Query execution failed: {e}",
            )
