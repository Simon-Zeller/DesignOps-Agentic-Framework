"""Tests for PrimitiveSpecGenerator CrewAI tool and create_primitive_scaffolding_agent."""
from __future__ import annotations

from pathlib import Path

import pytest

from daf.tools.primitive_spec_generator import PrimitiveSpecGenerator
from daf.agents.primitive_scaffolding import create_primitive_scaffolding_agent


# ---------------------------------------------------------------------------
# PrimitiveSpecGenerator tool tests
# ---------------------------------------------------------------------------


def test_primitive_spec_generator_tool_is_base_tool_subclass() -> None:
    from crewai.tools import BaseTool

    assert issubclass(PrimitiveSpecGenerator, BaseTool), (
        "PrimitiveSpecGenerator must be a subclass of crewai.tools.BaseTool"
    )


def test_primitive_spec_generator_tool_name() -> None:
    assert PrimitiveSpecGenerator().name == "PrimitiveSpecGenerator"


def test_primitive_spec_generator_tool_run_produces_files(tmp_path: Path) -> None:
    tool = PrimitiveSpecGenerator()
    result = tool.run(output_dir=str(tmp_path))
    assert isinstance(result, str) and result, "Tool run should return a non-empty string"
    yaml_files = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(yaml_files) == 11, (
        f"Expected 11 spec files, found {len(yaml_files)}: {yaml_files}"
    )


# ---------------------------------------------------------------------------
# Agent factory tests
# ---------------------------------------------------------------------------


def test_create_primitive_scaffolding_agent_returns_agent() -> None:
    from crewai import Agent

    agent = create_primitive_scaffolding_agent()
    assert isinstance(agent, Agent), (
        f"create_primitive_scaffolding_agent() should return a crewai.Agent, got {type(agent)}"
    )


def test_primitive_scaffolding_agent_has_tool() -> None:
    agent = create_primitive_scaffolding_agent()
    tool_types = [type(t) for t in agent.tools]
    assert PrimitiveSpecGenerator in tool_types, (
        f"PrimitiveSpecGenerator not found in agent tools: {tool_types}"
    )
