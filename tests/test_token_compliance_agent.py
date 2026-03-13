"""Unit tests for Agent 32: Token Compliance Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_token_compliance_agent_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.token_compliance_agent import create_token_compliance_agent

    agent = create_token_compliance_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert isinstance(agent, Agent)


def test_token_compliance_agent_role_contains_compliance(tmp_path):
    """Agent role contains the keyword 'compliance'."""
    from daf.agents.token_compliance_agent import create_token_compliance_agent

    agent = create_token_compliance_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "compliance" in agent.role.lower()


def test_token_compliance_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.token_compliance_agent import create_token_compliance_agent

    agent = create_token_compliance_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_token_compliance_agent_has_required_tools(tmp_path):
    """Agent tools include TokenComplianceScannerTool and TokenUsageMapper."""
    from daf.agents.token_compliance_agent import create_token_compliance_agent
    from daf.tools.token_compliance_scanner import TokenComplianceScannerTool
    from daf.tools.token_usage_mapper import TokenUsageMapper

    agent = create_token_compliance_agent("claude-3-5-haiku-20241022", str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert TokenComplianceScannerTool in tool_types
    assert TokenUsageMapper in tool_types
