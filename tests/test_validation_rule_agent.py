"""Unit tests for Validation Rule Agent factory (Agent 44, p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_MODEL = "claude-3-5-haiku-20241022"


def test_factory_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.validation_rule import create_validation_rule_agent

    agent = create_validation_rule_agent(_MODEL, str(tmp_path))
    assert isinstance(agent, Agent)


def test_agent_role_contains_validation_or_rule_keyword(tmp_path):
    """Agent role contains 'validation' or 'rule'."""
    from daf.agents.validation_rule import create_validation_rule_agent

    agent = create_validation_rule_agent(_MODEL, str(tmp_path))
    role_lower = agent.role.lower()
    assert "validation" in role_lower or "rule" in role_lower


def test_agent_uses_haiku_model(tmp_path):
    """Agent LLM is configured with the Haiku model."""
    from daf.agents.validation_rule import create_validation_rule_agent

    agent = create_validation_rule_agent(_MODEL, str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_agent_includes_required_tools(tmp_path):
    """Agent tool set includes RuleCompiler."""
    from daf.agents.validation_rule import create_validation_rule_agent
    from daf.tools.rule_compiler import RuleCompiler

    agent = create_validation_rule_agent(_MODEL, str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert RuleCompiler in tool_types
