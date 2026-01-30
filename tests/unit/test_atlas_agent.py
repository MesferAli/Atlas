"""Unit tests for the Atlas Agent."""

import pytest

from atlas.agents.atlas_agent import (
    AgentDeps,
    AtlasAgent,
    get_registered_tools,
)


class TestAtlasAgent:
    """Tests for the Atlas Agent."""

    def test_init(self):
        agent = AtlasAgent()
        assert agent.system_prompt is not None
        assert "Atlas" in agent.system_prompt or "MZX" in agent.system_prompt

    def test_available_tools(self):
        agent = AtlasAgent()
        tools = agent.available_tools
        assert isinstance(tools, dict)

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
        result = await agent.run("Query employee table")
        assert result.intent == "database_query"

    def test_classify_intent_database(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Query employee table") == "database_query"

    def test_classify_intent_database_sql(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Show me the sql for salary") == "database_query"

    def test_classify_intent_arabic(self):
        agent = AtlasAgent()
        assert agent._classify_intent("استعلام عن الموظفين") == "database_query"

    def test_classify_intent_general(self):
        agent = AtlasAgent()
        assert agent._classify_intent("Hello there") == "general"


class TestToolRegistry:
    """Tests for tool registration."""

    def test_registry_is_dict(self):
        tools = get_registered_tools()
        assert isinstance(tools, dict)
