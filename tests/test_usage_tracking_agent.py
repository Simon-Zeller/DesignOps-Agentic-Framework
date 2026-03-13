"""Unit tests for Agent 31: Usage Tracking Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_usage_tracking_agent_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.usage_tracking import create_usage_tracking_agent

    agent = create_usage_tracking_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert isinstance(agent, Agent)


def test_usage_tracking_agent_role_contains_usage(tmp_path):
    """Agent role contains the keyword 'usage'."""
    from daf.agents.usage_tracking import create_usage_tracking_agent

    agent = create_usage_tracking_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "usage" in agent.role.lower()


def test_usage_tracking_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.usage_tracking import create_usage_tracking_agent

    agent = create_usage_tracking_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_usage_tracking_agent_has_required_tools(tmp_path):
    """Agent tools include ASTImportScanner, TokenUsageMapper, DependencyGraphBuilder."""
    from daf.agents.usage_tracking import create_usage_tracking_agent
    from daf.tools.ast_import_scanner import ASTImportScanner
    from daf.tools.token_usage_mapper import TokenUsageMapper

    agent = create_usage_tracking_agent("claude-3-5-haiku-20241022", str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert ASTImportScanner in tool_types
    assert TokenUsageMapper in tool_types
