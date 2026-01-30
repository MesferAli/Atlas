"""SmolAgents Orchestrator — Autonomous tool-calling for complex data inquiries.

Enables the Atlas agent to chain multiple tool calls autonomously,
reasoning about which tools to invoke and how to combine results.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from atlas.agents.atlas_agent import (
    AgentDeps,
    AtlasAgent,
    AtlasAgentResult,
    get_registered_tools,
)
from atlas.core.mzx_protocol import MZXBaseModel, MZXSignature, generate_mzx_id


class OrchestrationStep(BaseModel):
    """A single step in the orchestration pipeline."""

    step_number: int
    tool_name: str | None = None
    input_summary: str = ""
    output_summary: str = ""
    success: bool = True
    error: str | None = None


class OrchestrationResult(MZXBaseModel):
    """Result of a multi-step orchestrated pipeline."""

    agent_name: str = "Atlas-Orchestrator"
    query: str
    steps: list[OrchestrationStep] = Field(default_factory=list)
    final_answer: str = ""
    total_tools_called: int = 0
    success: bool = True
    error: str | None = None


class AtlasOrchestrator:
    """Orchestrates multi-tool pipelines for complex queries.

    The orchestrator analyses a user query, plans a sequence of tool calls,
    executes them (potentially in parallel), and synthesizes results.
    """

    def __init__(self, deps: AgentDeps | None = None, max_steps: int = 5) -> None:
        self._agent = AtlasAgent(deps=deps)
        self._max_steps = max_steps
        self._deps = deps or AgentDeps()

    async def run(self, query: str) -> OrchestrationResult:
        """Run an orchestrated multi-tool pipeline.

        Args:
            query: Natural language query that may require multiple tools.

        Returns:
            OrchestrationResult with step-by-step execution trace.
        """
        mzx_id = generate_mzx_id()
        steps: list[OrchestrationStep] = []

        # Plan: determine which tools to call
        plan = self._plan(query)

        if not plan:
            # Single-step: delegate to the base agent
            result = await self._agent.run(query)
            return OrchestrationResult(
                query=query,
                steps=[
                    OrchestrationStep(
                        step_number=1,
                        tool_name=result.tool_calls[0]["tool"]
                        if result.tool_calls
                        else None,
                        input_summary=query[:200],
                        output_summary=result.final_answer[:200],
                        success=result.success,
                    )
                ],
                final_answer=result.final_answer,
                total_tools_called=len(result.tool_calls),
                success=result.success,
                mzx_auth=MZXSignature(mzx_id=mzx_id),
            )

        # Multi-step execution
        accumulated_context: list[dict[str, Any]] = []

        for i, tool_name in enumerate(plan, 1):
            if i > self._max_steps:
                break

            step = OrchestrationStep(
                step_number=i,
                tool_name=tool_name,
                input_summary=query[:200],
            )

            try:
                result = await self._agent.run(query)
                step.output_summary = result.final_answer[:200]
                step.success = result.success
                accumulated_context.extend(result.tool_calls)
            except Exception as e:
                step.success = False
                step.error = str(e)

            steps.append(step)

        final_answer = self._synthesize(query, accumulated_context)
        all_success = all(s.success for s in steps)

        return OrchestrationResult(
            query=query,
            steps=steps,
            final_answer=final_answer,
            total_tools_called=len(accumulated_context),
            success=all_success,
            mzx_auth=MZXSignature(mzx_id=mzx_id),
        )

    def _plan(self, query: str) -> list[str]:
        """Plan which tools to invoke for the query.

        Returns a list of tool names in execution order.
        An empty list means single-step delegation.
        """
        query_lower = query.lower()
        tools = get_registered_tools()
        plan: list[str] = []

        # Check if multiple tools are needed
        needs_image = any(
            kw in query_lower for kw in ["image", "blur", "quality", "luminance"]
        )
        needs_annotation = any(
            kw in query_lower for kw in ["annotation", "label", "overlap", "bbox"]
        )

        if needs_image and "audit_image_quality" in tools:
            plan.append("audit_image_quality")
        if needs_annotation and "verify_annotations" in tools:
            plan.append("verify_annotations")

        # Only return multi-step plan if more than one tool
        return plan if len(plan) > 1 else []

    def _synthesize(
        self, query: str, tool_results: list[dict[str, Any]]
    ) -> str:
        """Synthesize a final narrative answer from multiple tool results."""
        if not tool_results:
            return "No tools were executed for this query."

        parts: list[str] = []
        for t in tool_results:
            tool = t.get("tool", "unknown")
            if t.get("success"):
                result = t.get("result", {})
                summary = (
                    result.get("summary", str(result))
                    if isinstance(result, dict)
                    else str(result)
                )
                parts.append(f"{tool}: {summary}")
            else:
                parts.append(f"{tool}: ERROR — {t.get('error', 'Unknown')}")

        return " || ".join(parts)
