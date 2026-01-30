"""Unit tests for the Atlas Agent and tools."""

import pytest

from atlas.agents.atlas_agent import (
    AgentDeps,
    AtlasAgent,
    get_registered_tools,
)

# Import tools to trigger registration
import atlas.tools  # noqa: F401


class TestAtlasAgent:
    """Tests for the Atlas Agent."""

    def test_init(self):
        agent = AtlasAgent()
        assert agent.system_prompt is not None
        assert "Atlas" in agent.system_prompt or "MZX" in agent.system_prompt

    def test_available_tools(self):
        agent = AtlasAgent()
        tools = agent.available_tools
        assert "audit_image_quality" in tools
        assert "verify_annotations" in tools

    @pytest.mark.asyncio
    async def test_run_general(self):
        agent = AtlasAgent()
        result = await agent.run("Hello, what can you do?")
        assert result.agent_name == "Atlas"
        assert result.mzx_auth.mzx_id.startswith("MZX-")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_with_deps(self):
        deps = AgentDeps(user_id="test-user", user_role="ADMIN")
        agent = AtlasAgent(deps=deps)
        result = await agent.run("Tell me about image quality")
        assert result.intent == "audit_image_quality"

    def test_classify_intent_image(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Check blur on image") == "audit_image_quality"

    def test_classify_intent_annotation(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Verify annotation labels") == "verify_annotations"

    def test_classify_intent_database(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Query employee table") == "database_query"

    def test_classify_intent_arabic(self):
        agent = AtlasAgent()
        assert agent._classify_intent("استعلام عن الموظفين") == "database_query"


class TestToolRegistry:
    """Tests for tool registration."""

    def test_tools_registered(self):
        import atlas.tools  # noqa: F401

        tools = get_registered_tools()
        assert len(tools) >= 2
        assert "audit_image_quality" in tools
        assert "verify_annotations" in tools

    def test_tool_metadata(self):
        import atlas.tools  # noqa: F401

        tools = get_registered_tools()
        iq = tools["audit_image_quality"]
        assert iq.name == "audit_image_quality"
        assert "blur" in iq.description.lower() or "luminance" in iq.description.lower()
