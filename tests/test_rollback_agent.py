"""Tests for Agent 40 – Rollback Agent (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import crewai


def test_create_rollback_agent_returns_crewai_agent(tmp_path: Path) -> None:
    """Factory returns a crewai.Agent instance."""
    from daf.agents.rollback import create_rollback_agent

    agent = create_rollback_agent("claude-3-haiku-20240307", str(tmp_path))
    assert isinstance(agent, crewai.Agent)


def test_rollback_agent_role_keyword(tmp_path: Path) -> None:
    """Agent role contains 'rollback' or 'checkpoint' keyword."""
    from daf.agents.rollback import create_rollback_agent

    agent = create_rollback_agent("claude-3-haiku-20240307", str(tmp_path))
    role_lower = agent.role.lower()
    assert "rollback" in role_lower or "checkpoint" in role_lower or "generation" in role_lower


def test_rollback_agent_uses_haiku_model(tmp_path: Path) -> None:
    """Agent uses provided Haiku model string."""
    from daf.agents.rollback import create_rollback_agent

    model = "claude-3-haiku-20240307"
    agent = create_rollback_agent(model, str(tmp_path))
    assert agent.llm == model


def test_rollback_agent_has_required_tools(tmp_path: Path) -> None:
    """Agent tools include CheckpointCreator, RestoreExecutor, RollbackReporter."""
    from daf.agents.rollback import create_rollback_agent
    from daf.tools.checkpoint_creator import CheckpointCreator
    from daf.tools.restore_executor import RestoreExecutor
    from daf.tools.rollback_reporter import RollbackReporter

    agent = create_rollback_agent("claude-3-haiku-20240307", str(tmp_path))
    tool_types = [type(t) for t in agent.tools]
    assert CheckpointCreator in tool_types
    assert RestoreExecutor in tool_types
    assert RollbackReporter in tool_types


def test_rollback_agent_not_in_release_crew(tmp_path: Path) -> None:
    """Agent 40 is not included in create_release_crew agents list."""
    import json
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    (gate_dir / "quality-gates.json").write_text(
        json.dumps({"gates": [], "fatal_passed": 8, "fatal_failed": 0})
    )
    from daf.crews.release import create_release_crew

    crew = create_release_crew(str(tmp_path))
    for agent in crew.agents:
        role_lower = agent.role.lower()
        assert "rollback" not in role_lower
        assert "checkpoint manager" not in role_lower
