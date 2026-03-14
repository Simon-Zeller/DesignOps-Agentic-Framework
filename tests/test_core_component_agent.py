"""Tests for CoreComponentSpecGenerator (BaseTool) and core component agent (p07).

TDD approach: these tests define the agent/tool contract before implementation.
"""
from __future__ import annotations

import pytest
import crewai

from daf.tools.core_component_spec_generator import CoreComponentSpecGenerator
from daf.agents.core_component import create_core_component_agent, create_core_component_task


# ---------------------------------------------------------------------------
# CoreComponentSpecGenerator as BaseTool
# ---------------------------------------------------------------------------


def test_core_component_spec_generator_is_base_tool_subclass() -> None:
    from crewai.tools import BaseTool
    assert issubclass(CoreComponentSpecGenerator, BaseTool)


def test_core_component_spec_generator_name() -> None:
    assert CoreComponentSpecGenerator().name == "CoreComponentSpecGenerator"


def test_tool_run_produces_starter_files(tmp_path) -> None:
    tool = CoreComponentSpecGenerator()
    result = tool._run(
        scope="starter",
        output_dir=str(tmp_path),
        component_overrides_json="{}",
    )
    import os
    specs = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(specs) == 10
    assert "10" in result
    assert str(tmp_path) in result or "specs" in result


def test_tool_run_returns_error_string_for_invalid_scope(tmp_path) -> None:
    tool = CoreComponentSpecGenerator()
    result = tool._run(
        scope="invalid",
        output_dir=str(tmp_path),
        component_overrides_json="{}",
    )
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_core_component_agent_returns_agent() -> None:
    agent = create_core_component_agent()
    assert isinstance(agent, crewai.Agent)


@pytest.mark.integration
def test_core_component_agent_role() -> None:
    agent = create_core_component_agent()
    assert agent.role == "Core Component Agent"


@pytest.mark.integration
def test_core_component_agent_has_tool() -> None:
    agent = create_core_component_agent()
    tool_types = [type(t) for t in agent.tools]
    assert CoreComponentSpecGenerator in tool_types


def test_create_core_component_task_returns_task() -> None:
    task = create_core_component_task()
    assert isinstance(task, crewai.Task)


# ---------------------------------------------------------------------------
# Exports from daf.agents
# ---------------------------------------------------------------------------


def test_agent_and_task_exported_from_daf_agents() -> None:
    from daf.agents import create_core_component_agent, create_core_component_task  # noqa: F401
