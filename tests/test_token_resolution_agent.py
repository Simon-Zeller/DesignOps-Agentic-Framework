"""Unit tests for Token Resolution Agent factory (Agent 42, p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_MODEL = "claude-3-5-haiku-20241022"


def test_factory_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.token_resolution import create_token_resolution_agent

    agent = create_token_resolution_agent(_MODEL, str(tmp_path))
    assert isinstance(agent, Agent)


def test_agent_role_contains_token_keyword(tmp_path):
    """Agent role contains 'token'."""
    from daf.agents.token_resolution import create_token_resolution_agent

    agent = create_token_resolution_agent(_MODEL, str(tmp_path))
    assert "token" in agent.role.lower()


def test_agent_uses_haiku_model(tmp_path):
    """Agent LLM is configured with the Haiku model."""
    from daf.agents.token_resolution import create_token_resolution_agent

    agent = create_token_resolution_agent(_MODEL, str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_agent_includes_required_tools(tmp_path):
    """Agent tool set includes TokenGraphTraverser and SemanticMapper."""
    from daf.agents.token_resolution import create_token_resolution_agent
    from daf.tools.token_graph_traverser import TokenGraphTraverser
    from daf.tools.semantic_mapper import SemanticMapper

    agent = create_token_resolution_agent(_MODEL, str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert TokenGraphTraverser in tool_types
    assert SemanticMapper in tool_types
