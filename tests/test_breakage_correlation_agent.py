"""Unit tests for Agent 35: Breakage Correlation Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_breakage_correlation_agent_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.breakage_correlation import create_breakage_correlation_agent

    agent = create_breakage_correlation_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert isinstance(agent, Agent)


def test_breakage_correlation_agent_role_contains_breakage(tmp_path):
    """Agent role contains the keyword 'breakage'."""
    from daf.agents.breakage_correlation import create_breakage_correlation_agent

    agent = create_breakage_correlation_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert "breakage" in agent.role.lower()


def test_breakage_correlation_agent_uses_sonnet_model(tmp_path):
    """Agent is configured with a Sonnet model tier."""
    from daf.agents.breakage_correlation import create_breakage_correlation_agent

    agent = create_breakage_correlation_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert "sonnet" in agent.llm.model.lower()


def test_breakage_correlation_agent_has_dependency_chain_walker_tool(tmp_path):
    """Agent tools include DependencyChainWalker."""
    from daf.agents.breakage_correlation import create_breakage_correlation_agent
    from daf.tools.dependency_chain_walker import DependencyChainWalker

    agent = create_breakage_correlation_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert DependencyChainWalker in tool_types
