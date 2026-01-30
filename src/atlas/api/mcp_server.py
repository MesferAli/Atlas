"""MCP Server — Model Context Protocol server for local file/IDE interaction.

Implements the MCP protocol to allow IDE integrations and local tools
to interact with the Atlas agent and its tools. All responses are MZX-signed.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from atlas.agents.atlas_agent import AtlasAgent, AgentDeps, get_registered_tools
from atlas.core.mzx_protocol import MZXBaseModel, MZXSignature, generate_mzx_id

router = APIRouter(prefix="/mcp", tags=["MCP"])


# ---------------------------------------------------------------------------
# MCP Protocol Models
# ---------------------------------------------------------------------------
class MCPToolInput(BaseModel):
    """MCP tool input schema."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPRequest(BaseModel):
    """MCP protocol request."""

    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class MCPResponse(MZXBaseModel):
    """MCP protocol response with MZX traceability."""

    jsonrpc: str = "2.0"
    id: int | str
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# MCP Endpoints
# ---------------------------------------------------------------------------
@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    """List all available tools in the Atlas agent.

    Returns MCP-compatible tool definitions.
    """
    tools = get_registered_tools()
    mzx_id = generate_mzx_id()

    tool_list = [
        {
            "name": name,
            "description": meta.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Tool input"},
                },
            },
        }
        for name, meta in tools.items()
    ]

    return {
        "tools": tool_list,
        "mzx_id": mzx_id,
    }


@router.post("/call")
async def call_tool(request: MCPToolInput) -> dict[str, Any]:
    """Call a specific Atlas tool via MCP protocol.

    Args:
        request: Tool name and arguments.

    Returns:
        MXZ-signed tool execution result.
    """
    tools = get_registered_tools()
    if request.name not in tools:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.name}' not found. Available: {list(tools.keys())}",
        )

    agent = AtlasAgent()
    result = await agent.run(
        json.dumps({"tool": request.name, "args": request.arguments})
    )

    return {
        "tool": request.name,
        "result": result.model_dump(),
    }


@router.post("/message")
async def process_message(request: MCPRequest) -> MCPResponse:
    """Process an MCP protocol message.

    Supports methods:
    - tools/list: List available tools
    - tools/call: Execute a tool
    - agent/run: Run the Atlas agent with a message

    Args:
        request: MCP JSON-RPC request.

    Returns:
        MCPResponse with MZX traceability.
    """
    mzx_id = generate_mzx_id()

    if request.method == "tools/list":
        tools = get_registered_tools()
        return MCPResponse(
            id=request.id,
            result={
                "tools": [
                    {"name": n, "description": m.description}
                    for n, m in tools.items()
                ]
            },
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )

    elif request.method == "tools/call":
        tool_name = request.params.get("name", "")
        arguments = request.params.get("arguments", {})
        tools = get_registered_tools()

        if tool_name not in tools:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Tool not found: {tool_name}"},
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )

        agent = AtlasAgent()
        result = await agent.run(
            json.dumps({"tool": tool_name, "args": arguments})
        )
        return MCPResponse(
            id=request.id,
            result=result.model_dump(),
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )

    elif request.method == "agent/run":
        message = request.params.get("message", "")
        agent = AtlasAgent()
        result = await agent.run(message)
        return MCPResponse(
            id=request.id,
            result=result.model_dump(),
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )

    else:
        return MCPResponse(
            id=request.id,
            error={"code": -32601, "message": f"Unknown method: {request.method}"},
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )
