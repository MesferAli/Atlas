"""Atlas DB Guardrails API - FastAPI server for Atlas web interface."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from atlas.connectors.oracle.connector import OracleConnector, ReadOnlyViolationError

app = FastAPI(
    title="Atlas DB Guardrails API",
    description="Enterprise AI orchestration platform with read-only Oracle database access",
    version="1.0.0",
)

# Template directory path
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Global connector instance (configured via /connect endpoint)
_connector: OracleConnector | None = None


class QueryRequest(BaseModel):
    """Request model for SQL query execution."""

    sql_query: str


class ConnectionRequest(BaseModel):
    """Request model for database connection."""

    host: str
    port: int = 1521
    service_name: str
    user: str
    password: str


class QueryResponse(BaseModel):
    """Response model for successful query execution."""

    status: str
    data: list[dict]


class ValidationResponse(BaseModel):
    """Response model for query validation."""

    status: str
    valid: bool
    message: str


def _read_template(filename: str) -> str:
    """Read an HTML template file."""
    template_path = TEMPLATES_DIR / filename
    if not template_path.exists():
        raise HTTPException(status_code=404, detail=f"Template not found: {filename}")
    return template_path.read_text(encoding="utf-8")


# =============================================================================
# HTML Page Routes
# =============================================================================


@app.get("/", response_class=HTMLResponse)
def login_page():
    """Serve the login page (index.html)."""
    return _read_template("index.html")


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding_page():
    """Serve the onboarding/setup wizard page."""
    return _read_template("onboarding.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    """Serve the main dashboard page."""
    return _read_template("dashboard.html")


# =============================================================================
# API Routes
# =============================================================================


@app.post("/api/connect")
async def connect_database(request: ConnectionRequest):
    """
    Establish connection to Oracle database.

    Args:
        request: Connection parameters including host, port, service_name, user, password

    Returns:
        Connection status message
    """
    global _connector

    # Close existing connection if any
    if _connector:
        await _connector.close()

    dsn = f"{request.host}:{request.port}/{request.service_name}"

    try:
        _connector = OracleConnector(
            user=request.user,
            password=request.password,
            dsn=dsn,
        )
        await _connector.connect()
        return {"status": "success", "message": "Connected to Oracle database successfully"}
    except Exception as e:
        _connector = None
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@app.post("/api/disconnect")
async def disconnect_database():
    """Close the database connection."""
    global _connector

    if _connector:
        await _connector.close()
        _connector = None
        return {"status": "success", "message": "Disconnected from database"}

    return {"status": "info", "message": "No active connection"}


@app.post("/api/validate")
def validate_query(request: QueryRequest) -> ValidationResponse:
    """
    Validate a SQL query for read-only compliance.

    This endpoint checks if a query contains forbidden keywords (DDL/DML)
    without actually executing it.

    Args:
        request: SQL query to validate

    Returns:
        Validation result with status and message
    """
    # Create a temporary connector just for validation
    temp_connector = OracleConnector(user="", password="", dsn="")

    try:
        temp_connector.validate_query(request.sql_query)
        return ValidationResponse(
            status="success",
            valid=True,
            message="Query is valid (read-only SELECT statement)",
        )
    except ReadOnlyViolationError as e:
        return ValidationResponse(
            status="blocked",
            valid=False,
            message=str(e),
        )


@app.post("/api/execute")
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    Execute a protected (read-only) SQL query.

    This endpoint validates the query for read-only compliance and executes it
    if it passes validation. DDL/DML operations are blocked.

    Args:
        request: SQL query to execute

    Returns:
        Query results or error message

    Raises:
        HTTPException: If query is blocked or execution fails
    """
    global _connector

    if not _connector:
        raise HTTPException(
            status_code=400,
            detail="No database connection. Use /api/connect first.",
        )

    try:
        # validate_query is called internally by execute_query
        results = await _connector.execute_query(request.sql_query)
        return QueryResponse(status="success", data=results)
    except ReadOnlyViolationError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "blocked",
                "error": str(e),
                "guardrail": "ReadOnlyViolation",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error": str(e)},
        )


@app.get("/api/health")
def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "Atlas DB Guardrails",
        "version": "1.0.0",
        "connected": _connector is not None,
    }
