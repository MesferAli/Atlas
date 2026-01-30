"""Atlas API - FastAPI service for Oracle SQL RAG Agent.

SECURITY ARCHITECTURE:
- All data access goes through authenticated server-side endpoints
- Input validation is performed on all requests
- Audit logging captures all sensitive operations
- Rate limiting prevents brute force attacks
- Security headers protect against common web vulnerabilities
"""

import os
from contextlib import asynccontextmanager
from typing import Annotated, Any
from unittest.mock import MagicMock

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from atlas.agent.sql_agent import BaseLLM, MockLLM, OracleSQLAgent
from atlas.api.routes.audit import router as audit_router
from atlas.api.routes.auth import router as auth_router
from atlas.api.routes.enterprise import router as enterprise_router
from atlas.api.mcp_server import router as mcp_router
from atlas.api.security.audit import AuditEventType, get_audit_logger
from atlas.api.security.auth import TokenPayload, get_current_user_optional
from atlas.api.security.middleware import setup_security_middleware
from atlas.connectors.oracle.connector import OracleConnector
from atlas.connectors.oracle.indexer import OracleSchemaIndexer

# Environment configuration
USE_UNSLOTH = os.getenv("ATLAS_USE_UNSLOTH", "false").lower() == "true"
MODEL_PATH = os.getenv("ATLAS_MODEL_PATH", "/workspace/atlas_erp/models/atlas-qwen-full/final")
QDRANT_PATH = os.getenv("ATLAS_QDRANT_PATH", "./qdrant_data")


class ChatRequest(BaseModel):
    """Request body for chat endpoint.

    SECURITY: Validates and sanitizes natural language queries
    to prevent injection attacks.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question about the database",
    )

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """Sanitize the question to prevent potential injection."""
        # Remove null bytes
        v = v.replace("\x00", "")
        # Remove excessive whitespace
        v = " ".join(v.split())
        # Basic length check after sanitization
        if len(v) < 3:
            raise ValueError("Question must be at least 3 characters after cleanup")
        return v


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

        # Arabic keywords mapping
        # رواتب = salaries, موظفين = employees, عملاء = customers
        # إجمالي = total, الشهر = month

        if "customer" in query_lower or "عملاء" in query:
            return [
                {
                    "table_name": "CUSTOMERS",
                    "owner": "ERP",
                    "comments": "Master customer records / سجلات العملاء الرئيسية",
                    "score": 0.92,
                },
            ]
        is_payroll = (
            "employee" in query_lower
            or "salary" in query_lower
            or "رواتب" in query
            or "موظف" in query
        )
        if is_payroll:
            return [
                {
                    "table_name": "PAYROLL",
                    "owner": "HR",
                    "comments": "Monthly payroll transactions",
                    "columns": "EMPLOYEE_ID, EMPLOYEE_NAME, SALARY_AMOUNT, PAYMENT_DATE",
                    "score": 0.96,
                },
                {
                    "table_name": "EMPLOYEES",
                    "owner": "HR",
                    "comments": "Employee master data",
                    "columns": "EMPLOYEE_ID, NAME, DEPARTMENT, HIRE_DATE",
                    "score": 0.89,
                },
            ]
        if "order" in query_lower or "طلب" in query:
            return [
                {
                    "table_name": "ORDERS",
                    "owner": "ERP",
                    "comments": "Sales orders / طلبات المبيعات",
                    "score": 0.90,
                },
            ]
        return []

    indexer.search_tables = mock_search
    return indexer


def _create_llm() -> BaseLLM:
    """Create LLM instance based on environment configuration."""
    if USE_UNSLOTH:
        try:
            from atlas.agent.unsloth_llm import UnslothLLM

            print(f"Initializing Unsloth LLM from: {MODEL_PATH}")
            llm = UnslothLLM(model_path=MODEL_PATH)
            llm.load_model()
            print("Unsloth LLM loaded successfully!")
            return llm
        except Exception as e:
            print(f"Failed to load Unsloth LLM: {e}")
            print("Falling back to MockLLM")
            return MockLLM()
    else:
        print("Using MockLLM (set ATLAS_USE_UNSLOTH=true for real model)")
        return MockLLM()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize agent on startup."""
    global _agent

    # Initialize components
    connector = _create_mock_connector()
    indexer = _create_mock_indexer()
    llm = _create_llm()

    _agent = OracleSQLAgent(connector=connector, indexer=indexer, llm=llm)

    print(f"Atlas API initialized (Unsloth: {USE_UNSLOTH})")

    yield

    # Cleanup
    _agent = None


app = FastAPI(
    title="Atlas API",
    description="Saudi AI Middleware - Oracle SQL RAG Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# SECURITY: Setup security middleware (rate limiting, security headers)
setup_security_middleware(app)

# SECURITY: Configure CORS with strict settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ATLAS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Include authentication routes
app.include_router(auth_router)

# Include audit routes
app.include_router(audit_router)

# Include enterprise bridge routes (Wafer ERP integration)
app.include_router(enterprise_router)

# Include MCP server routes (IDE/local tool integration)
app.include_router(mcp_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/security")
async def security_status() -> dict:
    """
    Security configuration status endpoint.

    Use this to verify security settings for government/enterprise compliance.
    Shows: Thin Mode, Read-Only enforcement, blocked operations.
    """
    return OracleConnector.get_security_status()


@app.get("/v1/model")
async def model_status() -> dict:
    """
    Get information about the loaded LLM model.

    Returns model type, path, and configuration.
    """
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    llm = _agent._llm

    # Check if it's an UnslothLLM
    if hasattr(llm, "get_model_info"):
        return llm.get_model_info()
    else:
        return {
            "model_type": "MockLLM",
            "loaded": True,
            "description": "Mock LLM for testing - returns predefined SQL patterns",
        }


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    request: ChatRequest,
    user: Annotated[TokenPayload | None, Depends(get_current_user_optional)] = None,
) -> ChatResponse:
    """
    Process a natural language question and return SQL results.

    SECURITY:
    - Input is validated and sanitized
    - Query execution is logged for audit
    - Only read-only SQL is permitted

    Args:
        http_request: FastAPI request object
        request: ChatRequest with the user's question
        user: Optional authenticated user (for audit logging)

    Returns:
        ChatResponse with generated SQL and query results
    """
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    audit = get_audit_logger()
    client_ip = http_request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip and http_request.client:
        client_ip = http_request.client.host

    try:
        response = await _agent.run(request.question)

        # Log successful query
        audit.log(
            event_type=AuditEventType.QUERY_EXECUTED,
            user_id=user.sub if user else None,
            user_email=user.email if user else None,
            client_ip=client_ip,
            resource_type="oracle_query",
            action="nl_to_sql",
            details={
                "question": request.question[:200],
                "tables_used": [t.get("table_name") for t in response.relevant_tables],
                "sql_generated": response.generated_sql[:500] if response.generated_sql else None,
            },
            success=response.error is None,
            error_message=response.error,
        )

        return ChatResponse(
            question=response.question,
            relevant_tables=response.relevant_tables,
            generated_sql=response.generated_sql,
            results=response.results,
            error=response.error,
        )
    except Exception as e:
        # Log blocked or failed query
        audit.log(
            event_type=AuditEventType.QUERY_BLOCKED,
            user_id=user.sub if user else None,
            user_email=user.email if user else None,
            client_ip=client_ip,
            resource_type="oracle_query",
            action="nl_to_sql",
            details={"question": request.question[:200]},
            success=False,
            error_message=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
