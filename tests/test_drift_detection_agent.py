"""Unit tests for Agent 33: Drift Detection Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_drift_detection_agent_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.drift_detection import create_drift_detection_agent

    agent = create_drift_detection_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert isinstance(agent, Agent)


def test_drift_detection_agent_role_contains_drift(tmp_path):
    """Agent role contains the keyword 'drift'."""
    from daf.agents.drift_detection import create_drift_detection_agent

    agent = create_drift_detection_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert "drift" in agent.role.lower()


def test_drift_detection_agent_uses_sonnet_model(tmp_path):
    """Agent is configured with a Sonnet model tier."""
    from daf.agents.drift_detection import create_drift_detection_agent

    agent = create_drift_detection_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert "sonnet" in agent.llm.model.lower()


def test_drift_detection_agent_has_required_tools(tmp_path):
    """Agent tools include StructuralComparator, DriftReporter, and DocPatcher."""
    from daf.agents.drift_detection import create_drift_detection_agent
    from daf.tools.doc_patcher import DocPatcher
    from daf.tools.drift_reporter import DriftReporter
    from daf.tools.structural_comparator import StructuralComparator

    agent = create_drift_detection_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert StructuralComparator in tool_types
    assert DriftReporter in tool_types
    assert DocPatcher in tool_types
