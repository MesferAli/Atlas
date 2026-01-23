"""Atlas DB Guardrails API - FastAPI application for protected SQL execution.

This module provides a REST API for executing SQL queries through the
enterprise guardrails system, ensuring timeout and row-limit enforcement.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from atlas.api.safe_db_connector import execute_protected_query

app = FastAPI(
    title="Atlas DB Guardrails API",
    description="Enterprise-grade SQL execution with timeout and row-limit protection.",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    """Request model for SQL query execution.

    Attributes:
        sql_query: The SQL SELECT query to execute.
    """

    sql_query: str = Field(..., min_length=1, description="SQL SELECT query to execute")


class QueryResponse(BaseModel):
    """Response model for successful query execution.

    Attributes:
        status: Execution status ('success').
        data_count: Number of rows returned.
        data: List of row dictionaries.
    """

    status: str
    data_count: int
    data: list[dict]


class HealthResponse(BaseModel):
    """Response model for health check endpoint.

    Attributes:
        status: Service status.
        system: System description.
    """

    status: str
    system: str


@app.get("/", response_model=HealthResponse)
def home() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse indicating service status.
    """
    return HealthResponse(status="online", system="Atlas Guardrails Active")


@app.post("/execute", response_model=QueryResponse)
async def run_query(request: QueryRequest) -> QueryResponse:
    """Execute a SQL query through the guardrails system.

    This endpoint validates the query, enforces timeout and row limits,
    and returns the results or an appropriate error.

    Args:
        request: QueryRequest containing the SQL query.

    Returns:
        QueryResponse with query results.

    Raises:
        HTTPException: If the query fails validation or execution.
    """
    print(f"[API] Received Query: {request.sql_query}")

    result = await execute_protected_query(request.sql_query)

    if result["status"] == "success":
        return QueryResponse(
            status="success",
            data_count=len(result["data"]),
            data=result["data"],
        )
    else:
        # Guardrail triggered or validation failed
        raise HTTPException(status_code=400, detail=result["error"])
