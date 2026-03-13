"""Tests for Agent 27: Workflow Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_workflow_agent_has_correct_tools(tmp_path):
    """Agent tools include WorkflowStateMachine and GateMapper."""
    from daf.agents.workflow import create_workflow_agent
    from daf.tools.workflow_state_machine import WorkflowStateMachine
    from daf.tools.gate_mapper import GateMapper

    agent = create_workflow_agent("claude-3-5-haiku-20241022", str(tmp_path))

    tool_types = {type(t) for t in agent.tools}
    assert WorkflowStateMachine in tool_types
    assert GateMapper in tool_types


def test_workflow_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.workflow import create_workflow_agent

    agent = create_workflow_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()
