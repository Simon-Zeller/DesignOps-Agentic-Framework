"""Tests for ExitCriteriaAgent factory (p19-exit-criteria, TDD red phase)."""
from __future__ import annotations

import pytest
import crewai


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_create_exit_criteria_agent_returns_agent(tmp_path) -> None:
    """create_exit_criteria_agent returns a crewai.Agent instance."""
    from daf.agents.exit_criteria import create_exit_criteria_agent

    agent = create_exit_criteria_agent("claude-3-haiku-20240307", str(tmp_path))

    assert isinstance(agent, crewai.Agent)


def test_exit_criteria_agent_has_exactly_two_tools(tmp_path) -> None:
    """The exit criteria agent has exactly two tools."""
    from daf.agents.exit_criteria import create_exit_criteria_agent

    agent = create_exit_criteria_agent("claude-3-haiku-20240307", str(tmp_path))

    assert len(agent.tools) == 2
