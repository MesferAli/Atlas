"""Atlas Agent — Primary MZX-certified AI agent using Pydantic-AI patterns.

This agent orchestrates tool calls for enterprise data operations
and natural language queries against enterprise databases. Every interaction
is signed with the MZX protocol for end-to-end traceability.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from atlas.core.config import get_config
from atlas.core.mzx_protocol import (
    MZXAgentResponse,
    MZXBaseModel,
    MZXSignature,
    generate_mzx_id,
)


# ---------------------------------------------------------------------------
# Agent Dependencies (injected context)
# ---------------------------------------------------------------------------
@dataclass
class AgentDeps:
    """Dependencies injected into the Atlas agent at runtime."""

    user_id: str | None = None
    user_role: str = "ANALYST"
    client_ip: str = "127.0.0.1"
    session_id: str = field(default_factory=lambda: generate_mzx_id())


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------
class ToolDefinition(BaseModel):
    """Metadata for a registered tool."""

    name: str
    description: str
    is_async: bool = False


_tool_registry: dict[str, Any] = {}
_tool_meta: dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    description: str = "",
    is_async: bool = False,
):
    """Decorator to register a callable as an Atlas agent tool.

    Usage:
        @register_tool("audit_image_quality", "Detect blur and luminance issues")
        async def audit_image_quality(image_path: str) -> dict:
            ...
    """

    def decorator(func):
        _tool_registry[name] = func
        _tool_meta[name] = ToolDefinition(
            name=name,
            description=description or func.__doc__ or "",
            is_async=is_async or asyncio.iscoroutinefunction(func),
        )
        return func

    return decorator


def get_registered_tools() -> dict[str, ToolDefinition]:
    """Return metadata for all registered tools."""
    return dict(_tool_meta)


# ---------------------------------------------------------------------------
# Atlas Agent
# ---------------------------------------------------------------------------
class ToolCallRequest(BaseModel):
    """A request to call a specific tool."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AtlasAgentResult(MZXBaseModel):
    """Result returned by the Atlas Agent after processing a request."""

    agent_name: str = "Atlas"
    intent: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    final_answer: str = ""
    success: bool = True
    error: str | None = None


class AtlasAgent:
    """Primary MZX-certified AI agent for the XCircle ecosystem.

    System prompt: "You are Atlas, an MZX-certified AI teammate."

    Capabilities:
    - Natural language understanding for enterprise data queries
    - Extensible tool registry for enterprise operations
    - MZX-signed traceability on every interaction
    """

    def __init__(self, deps: AgentDeps | None = None) -> None:
        cfg = get_config()
        self._system_prompt = cfg.agent.system_prompt
        self._agent_name = cfg.agent.name
        self._max_tokens = cfg.agent.max_tokens
        self._temperature = cfg.agent.temperature
        self._deps = deps or AgentDeps()

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @property
    def available_tools(self) -> dict[str, ToolDefinition]:
        return get_registered_tools()

    async def run(self, user_message: str) -> AtlasAgentResult:
        """Process a user message, optionally calling tools.

        The agent analyses the intent, determines which tools to call,
        executes them, and returns an MZX-signed result.

        Args:
            user_message: Natural language input from the user.

        Returns:
            AtlasAgentResult with tool call results and final answer.
        """
        mzx_id = generate_mzx_id()
        intent = self._classify_intent(user_message)

        tool_results: list[dict[str, Any]] = []
        tool_name = self._select_tool(intent, user_message)

        if tool_name and tool_name in _tool_registry:
            try:
                result = await self._call_tool(tool_name, user_message)
                tool_results.append(
                    {"tool": tool_name, "result": result, "success": True}
                )
            except Exception as e:
                tool_results.append(
                    {"tool": tool_name, "error": str(e), "success": False}
                )

        final_answer = self._compose_answer(intent, tool_results, user_message)

        return AtlasAgentResult(
            agent_name=self._agent_name,
            intent=intent,
            tool_calls=tool_results,
            final_answer=final_answer,
            success=all(t.get("success", False) for t in tool_results)
            if tool_results
            else True,
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )

    def _classify_intent(self, message: str) -> str:
        """Classify the user's intent from the message."""
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["query", "sql", "table", "employee", "salary"]):
            return "database_query"
        if any(kw in msg_lower for kw in ["استعلام", "جدول", "موظف", "رواتب"]):
            return "database_query"
        return "general"

    def _select_tool(self, intent: str, message: str) -> str | None:
        """Select the best tool for the classified intent."""
        intent_tool_map = {
            "database_query": "database_query",
        }
        tool = intent_tool_map.get(intent)
        if tool and tool in _tool_registry:
            return tool
        return None

    async def _call_tool(self, tool_name: str, user_message: str) -> Any:
        """Execute a registered tool."""
        func = _tool_registry[tool_name]
        meta = _tool_meta[tool_name]

        if meta.is_async:
            return await func(user_message)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, user_message)

    def _compose_answer(
        self,
        intent: str,
        tool_results: list[dict[str, Any]],
        user_message: str,
    ) -> str:
        """Compose a final narrative answer from tool results."""
        if not tool_results:
            return (
                f"I understood your request regarding '{intent}'. "
                f"No specific tool was needed. How can I help further?"
            )

        successful = [t for t in tool_results if t.get("success")]
        failed = [t for t in tool_results if not t.get("success")]

        parts: list[str] = []
        for t in successful:
            result = t.get("result", {})
            if isinstance(result, dict):
                summary = result.get("summary", str(result))
            else:
                summary = str(result)
            parts.append(f"[{t['tool']}] {summary}")

        for t in failed:
            parts.append(f"[{t['tool']}] Failed: {t.get('error', 'Unknown error')}")

        return " | ".join(parts)
