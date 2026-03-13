"""Structural tests for Agent 5 (Pipeline Configuration Agent) factory.

All tests are unit tests — no LLM calls, no live Anthropic API.
Tests verify the agent factory returns correct structures and the
tool classes are valid BaseTool subclasses.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Agent factory tests
# ---------------------------------------------------------------------------

def test_create_agent_returns_agent_with_correct_role(monkeypatch):
    from crewai import Agent
    from daf.agents.pipeline_config import create_pipeline_config_agent
    from daf.tools.config_generator import ConfigGenerator
    from daf.tools.project_scaffolder import ProjectScaffolder

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    agent = create_pipeline_config_agent()
    assert isinstance(agent, Agent)
    assert agent.role == "Pipeline Configuration Agent"
    tool_types = [type(t) for t in agent.tools]
    assert ConfigGenerator in tool_types
    assert ProjectScaffolder in tool_types


def test_create_agent_uses_tier2_model_env_var(monkeypatch):
    from unittest.mock import MagicMock, patch
    from daf.agents.pipeline_config import create_pipeline_config_agent

    monkeypatch.setenv("DAF_TIER2_MODEL", "claude-sonnet-4-custom")

    # Patch Agent constructor to avoid LLM instantiation without API key
    with patch("daf.agents.pipeline_config.Agent") as MockAgent:
        MockAgent.return_value = MagicMock()
        create_pipeline_config_agent()
        _, kwargs = MockAgent.call_args
        assert kwargs.get("llm") == "claude-sonnet-4-custom"


# ---------------------------------------------------------------------------
# Task factory tests
# ---------------------------------------------------------------------------

def test_create_task_returns_task_instance():
    from crewai import Task
    from daf.agents.pipeline_config import create_pipeline_config_task

    task = create_pipeline_config_task(output_dir=".", brand_profile_path="./brand-profile.json")
    assert isinstance(task, Task)
    assert "ConfigGenerator" in task.description
    assert "ProjectScaffolder" in task.description


def test_create_task_includes_context_tasks():
    from unittest.mock import patch
    from crewai import Task
    from daf.agents.pipeline_config import create_pipeline_config_task

    # Create a real minimal Task to use as context (MagicMock fails crewai validation)
    upstream_task = Task(
        description="Upstream task for context",
        expected_output="output",
    )
    task = create_pipeline_config_task(
        output_dir=".",
        brand_profile_path="./brand-profile.json",
        context_tasks=[upstream_task],
    )
    assert task.context is not None
    assert upstream_task in task.context


# ---------------------------------------------------------------------------
# BaseTool structural tests
# ---------------------------------------------------------------------------

def test_config_generator_is_valid_basetool():
    from crewai.tools import BaseTool
    from daf.tools.config_generator import ConfigGenerator

    tool = ConfigGenerator()
    assert isinstance(tool, BaseTool)
    assert len(tool.name) > 0
    assert len(tool.description) > 0


def test_project_scaffolder_is_valid_basetool():
    from crewai.tools import BaseTool
    from daf.tools.project_scaffolder import ProjectScaffolder

    tool = ProjectScaffolder()
    assert isinstance(tool, BaseTool)
    assert len(tool.name) > 0
    assert len(tool.description) > 0
