"""Unit tests for Registry Maintenance Agent factory (Agent 41, p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


_MODEL = "claude-3-5-haiku-20241022"


def test_factory_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.registry_maintenance import create_registry_maintenance_agent

    agent = create_registry_maintenance_agent(_MODEL, str(tmp_path))
    assert isinstance(agent, Agent)


def test_agent_role_contains_registry_keyword(tmp_path):
    """Agent role contains 'registry'."""
    from daf.agents.registry_maintenance import create_registry_maintenance_agent

    agent = create_registry_maintenance_agent(_MODEL, str(tmp_path))
    assert "registry" in agent.role.lower()


def test_agent_uses_haiku_model(tmp_path):
    """Agent LLM is configured with the Haiku model."""
    from daf.agents.registry_maintenance import create_registry_maintenance_agent

    agent = create_registry_maintenance_agent(_MODEL, str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_agent_includes_required_tools(tmp_path):
    """Agent tool set includes SpecIndexer, ExampleCodeGenerator, and RegistryBuilder."""
    from daf.agents.registry_maintenance import create_registry_maintenance_agent
    from daf.tools.spec_indexer import SpecIndexer
    from daf.tools.example_code_generator import ExampleCodeGenerator
    from daf.tools.registry_builder import RegistryBuilder

    agent = create_registry_maintenance_agent(_MODEL, str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert SpecIndexer in tool_types
    assert ExampleCodeGenerator in tool_types
    assert RegistryBuilder in tool_types
