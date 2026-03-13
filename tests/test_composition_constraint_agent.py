"""Unit tests for Composition Constraint Agent factory (Agent 43, p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_MODEL = "claude-3-5-sonnet-20241022"


def test_factory_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.composition_constraint import create_composition_constraint_agent

    agent = create_composition_constraint_agent(_MODEL, str(tmp_path))
    assert isinstance(agent, Agent)


def test_agent_role_contains_composition_keyword(tmp_path):
    """Agent role contains 'composition'."""
    from daf.agents.composition_constraint import create_composition_constraint_agent

    agent = create_composition_constraint_agent(_MODEL, str(tmp_path))
    assert "composition" in agent.role.lower()


def test_agent_uses_sonnet_model(tmp_path):
    """Agent LLM is configured with the Sonnet model."""
    from daf.agents.composition_constraint import create_composition_constraint_agent

    agent = create_composition_constraint_agent(_MODEL, str(tmp_path))
    assert "sonnet" in agent.llm.model.lower()


def test_agent_includes_required_tools(tmp_path):
    """Agent tool set includes CompositionRuleExtractor and TreeValidator."""
    from daf.agents.composition_constraint import create_composition_constraint_agent
    from daf.tools.composition_rule_extractor import CompositionRuleExtractor
    from daf.tools.tree_validator import TreeValidator

    agent = create_composition_constraint_agent(_MODEL, str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert CompositionRuleExtractor in tool_types
    assert TreeValidator in tool_types
