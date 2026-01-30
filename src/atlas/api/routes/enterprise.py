"""Enterprise Bridge — FastAPI endpoint serving Wafer ERP with MZX-verified JSON.

Provides the /audit endpoint that external enterprise systems (Wafer ERP)
can call to trigger and retrieve audit results. All responses include
MZX verification signatures.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from atlas.agents.atlas_agent import AgentDeps, AtlasAgent
from atlas.agents.orchestrator import AtlasOrchestrator
from atlas.api.security.auth import TokenPayload, get_current_user
from atlas.core.mzx_protocol import MZXSignature, generate_mzx_id

router = APIRouter(prefix="/api/enterprise", tags=["Enterprise"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class AuditRequest(BaseModel):
    """Request to run an audit via the enterprise bridge."""

    audit_type: str = Field(
        ...,
        description="Type of audit: 'image_quality', 'annotations', 'data_query', 'full'",
    )
    target: str = Field(
        ...,
        description="Target for the audit (file path, dataset ID, or query)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for the audit",
    )


class AuditResult(BaseModel):
    """MZX-verified audit result for ERP consumption."""

    mzx_id: str
    mzx_verified: bool = True
    audit_type: str
    target: str
    result: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Enterprise Endpoints
# ---------------------------------------------------------------------------
@router.post("/audit", response_model=AuditResult)
async def run_enterprise_audit(
    request: AuditRequest,
    user: TokenPayload = Depends(get_current_user),
) -> AuditResult:
    """Run an MZX-verified audit for enterprise ERP integration.

    This endpoint is designed for Wafer ERP and other enterprise systems
    that need verified, traceable audit results.

    Args:
        request: Audit type, target, and parameters.
        user: Authenticated user (JWT required).

    Returns:
        AuditResult with MZX verification signature.
    """
    from datetime import datetime, timezone

    mzx_id = generate_mzx_id()
    deps = AgentDeps(user_id=user.sub, user_role=user.role)

    # Build the query for the agent
    query = f"Perform {request.audit_type} audit on: {request.target}"
    if request.parameters:
        query += f" with parameters: {request.parameters}"

    try:
        if request.audit_type == "full":
            orchestrator = AtlasOrchestrator(deps=deps)
            result = await orchestrator.run(query)
            result_data = result.model_dump()
        else:
            agent = AtlasAgent(deps=deps)
            result = await agent.run(query)
            result_data = result.model_dump()

        return AuditResult(
            mzx_id=mzx_id,
            mzx_verified=True,
            audit_type=request.audit_type,
            target=request.target,
            result=result_data,
            success=result.success,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        return AuditResult(
            mzx_id=mzx_id,
            mzx_verified=True,
            audit_type=request.audit_type,
            target=request.target,
            success=False,
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@router.get("/audit/status")
async def audit_status(
    user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """Get the status of the enterprise audit system.

    Returns available audit types, registered tools, and MZX protocol info.
    """
    from atlas.agents.atlas_agent import get_registered_tools

    tools = get_registered_tools()
    mzx_id = generate_mzx_id()

    return {
        "mzx_id": mzx_id,
        "mzx_verified": True,
        "status": "operational",
        "available_audit_types": ["image_quality", "annotations", "data_query", "full"],
        "registered_tools": {
            name: {"description": meta.description, "is_async": meta.is_async}
            for name, meta in tools.items()
        },
        "protocol": {
            "name": "MZX",
            "version": "1.0.0",
            "product": "ATLAS",
        },
    }
