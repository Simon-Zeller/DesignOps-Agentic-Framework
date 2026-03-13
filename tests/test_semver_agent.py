"""Tests for Agent 36 – Semver Agent (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import crewai
import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_create_semver_agent_returns_crewai_agent(tmp_path: Path) -> None:
    """Factory returns a crewai.Agent instance."""
    from daf.agents.semver import create_semver_agent

    agent = create_semver_agent("claude-3-haiku-20240307", str(tmp_path))
    assert isinstance(agent, crewai.Agent)


def test_semver_agent_role_keyword(tmp_path: Path) -> None:
    """Agent role contains 'version' keyword."""
    from daf.agents.semver import create_semver_agent

    agent = create_semver_agent("claude-3-haiku-20240307", str(tmp_path))
    assert "version" in agent.role.lower()


def test_semver_agent_uses_haiku_model(tmp_path: Path) -> None:
    """Agent uses provided Haiku model string."""
    from daf.agents.semver import create_semver_agent

    model = "claude-3-haiku-20240307"
    agent = create_semver_agent(model, str(tmp_path))
    assert "haiku" in agent.llm.model.lower()


def test_semver_agent_has_gate_status_reader_and_version_calculator(tmp_path: Path) -> None:
    """Agent tools include GateStatusReader and VersionCalculator."""
    from daf.agents.semver import create_semver_agent
    from daf.tools.gate_status_reader import GateStatusReader
    from daf.tools.version_calculator import VersionCalculator

    agent = create_semver_agent("claude-3-haiku-20240307", str(tmp_path))
    tool_types = [type(t) for t in agent.tools]
    assert GateStatusReader in tool_types
    assert VersionCalculator in tool_types
