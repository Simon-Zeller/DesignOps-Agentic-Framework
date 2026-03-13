"""Unit tests for Agent 34: Pipeline Completeness Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_pipeline_completeness_agent_returns_crewai_agent(tmp_path):
    """Factory returns a crewai.Agent instance."""
    from crewai import Agent

    from daf.agents.pipeline_completeness import create_pipeline_completeness_agent

    agent = create_pipeline_completeness_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert isinstance(agent, Agent)


def test_pipeline_completeness_agent_role_contains_completeness(tmp_path):
    """Agent role contains the keyword 'completeness'."""
    from daf.agents.pipeline_completeness import create_pipeline_completeness_agent

    agent = create_pipeline_completeness_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "completeness" in agent.role.lower()


def test_pipeline_completeness_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.pipeline_completeness import create_pipeline_completeness_agent

    agent = create_pipeline_completeness_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_pipeline_completeness_agent_has_pipeline_stage_tracker_tool(tmp_path):
    """Agent tools include PipelineStageTracker."""
    from daf.agents.pipeline_completeness import create_pipeline_completeness_agent
    from daf.tools.pipeline_stage_tracker import PipelineStageTracker

    agent = create_pipeline_completeness_agent("claude-3-5-haiku-20241022", str(tmp_path))
    tool_types = {type(t) for t in agent.tools}
    assert PipelineStageTracker in tool_types
