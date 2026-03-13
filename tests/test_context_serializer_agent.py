"""Unit tests for Context Serializer Agent factory (Agent 45, p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_MODEL = "claude-3-5-sonnet-20241022"


def test_factory_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.context_serializer import create_context_serializer_agent

    agent = create_context_serializer_agent(_MODEL, str(tmp_path))
    assert isinstance(agent, Agent)


def test_agent_role_contains_context_keyword(tmp_path):
    """Agent role contains 'context' or 'serializer'."""
    from daf.agents.context_serializer import create_context_serializer_agent

    agent = create_context_serializer_agent(_MODEL, str(tmp_path))
    role_lower = agent.role.lower()
    assert "context" in role_lower or "serializer" in role_lower or "packager" in role_lower


def test_agent_uses_sonnet_model(tmp_path):
    """Agent LLM is configured with the Sonnet model."""
    from daf.agents.context_serializer import create_context_serializer_agent

    agent = create_context_serializer_agent(_MODEL, str(tmp_path))
    assert "sonnet" in agent.llm.model.lower()


def test_agent_includes_required_tools(tmp_path):
    """Agent tool set includes ContextFormatter, TokenBudgetOptimizer, MultiFormatSerializer."""
    from daf.agents.context_serializer import create_context_serializer_agent
    from daf.tools.context_formatter import ContextFormatter
    from daf.tools.token_budget_optimizer import TokenBudgetOptimizer
    from daf.tools.multi_format_serializer import MultiFormatSerializer

    agent = create_context_serializer_agent(_MODEL, str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert ContextFormatter in tool_types
    assert TokenBudgetOptimizer in tool_types
    assert MultiFormatSerializer in tool_types
