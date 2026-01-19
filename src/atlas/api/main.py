"""Atlas API - FastAPI service for Oracle SQL RAG Agent."""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from atlas.agent.sql_agent import MockLLM, OracleSQLAgent
from atlas.connectors.oracle.connector import OracleConnector
from atlas.connectors.oracle.indexer import OracleSchemaIndexer


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    question: str


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    question: str
    relevant_tables: list[dict[str, Any]]
    generated_sql: str
    results: list[dict[str, Any]] | None
    error: str | None = None


# Global agent instance
_agent: OracleSQLAgent | None = None


def _create_mock_connector() -> OracleConnector:
    """Create a mock OracleConnector for demo purposes."""
    connector = MagicMock(spec=OracleConnector)

    # Use the real validate_query method
    real_connector = OracleConnector.__new__(OracleConnector)
    connector.validate_query = real_connector.validate_query

    async def mock_execute(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        connector.validate_query(sql)
        if "CUSTOMERS" in sql.upper():
            return [
                {"CUSTOMER_ID": 1, "NAME": "Acme Corp", "TOTAL_PURCHASES": 150000},
                {"CUSTOMER_ID": 2, "NAME": "GlobalTech", "TOTAL_PURCHASES": 120000},
                {"CUSTOMER_ID": 3, "NAME": "Saudi Industries", "TOTAL_PURCHASES": 95000},
            ]
        return [{"RESULT": "Query executed"}]

    connector.execute_query = mock_execute
    return connector


def _create_mock_indexer() -> OracleSchemaIndexer:
    """Create a mock OracleSchemaIndexer for demo purposes."""
    indexer = MagicMock(spec=OracleSchemaIndexer)

    def mock_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()
        if "customer" in query_lower:
            return [
                {
                    "table_name": "CUSTOMERS",
                    "owner": "ERP",
                    "comments": "Master customer records",
                    "score": 0.92,
                },
            ]
        elif "employee" in query_lower:
            return [
                {
                    "table_name": "EMPLOYEES",
                    "owner": "HR",
                    "comments": "Employee master data",
                    "score": 0.95,
                },
            ]
        return []

    indexer.search_tables = mock_search
    return indexer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize agent on startup."""
    global _agent

    # Initialize mock components for demo
    connector = _create_mock_connector()
    indexer = _create_mock_indexer()
    llm = MockLLM()

    _agent = OracleSQLAgent(connector=connector, indexer=indexer, llm=llm)

    yield

    # Cleanup
    _agent = None


app = FastAPI(
    title="Atlas API",
    description="Saudi AI Middleware - Oracle SQL RAG Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a natural language question and return SQL results.

    Args:
        request: ChatRequest with the user's question

    Returns:
        ChatResponse with generated SQL and query results
    """
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    response = await _agent.run(request.question)

    return ChatResponse(
        question=response.question,
        relevant_tables=response.relevant_tables,
        generated_sql=response.generated_sql,
        results=response.results,
        error=response.error,
    )
