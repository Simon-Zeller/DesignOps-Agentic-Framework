"""Tests for Agent 37 – Release Changelog Agent (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import crewai


def test_create_release_changelog_agent_returns_crewai_agent(tmp_path: Path) -> None:
    """Factory returns a crewai.Agent instance."""
    from daf.agents.release_changelog import create_release_changelog_agent

    agent = create_release_changelog_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert isinstance(agent, crewai.Agent)


def test_release_changelog_agent_role_keyword(tmp_path: Path) -> None:
    """Agent role contains 'changelog' or 'inventory' keyword."""
    from daf.agents.release_changelog import create_release_changelog_agent

    agent = create_release_changelog_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    role_lower = agent.role.lower()
    assert "changelog" in role_lower or "inventory" in role_lower or "release" in role_lower


def test_release_changelog_agent_uses_sonnet_model(tmp_path: Path) -> None:
    """Agent uses provided Sonnet model string."""
    from daf.agents.release_changelog import create_release_changelog_agent

    model = "claude-3-5-sonnet-20241022"
    agent = create_release_changelog_agent(model, str(tmp_path))
    assert agent.llm == model


def test_release_changelog_agent_has_required_tools(tmp_path: Path) -> None:
    """Agent tools include ComponentInventoryReader, QualityReportParser, ProseGenerator."""
    from daf.agents.release_changelog import create_release_changelog_agent
    from daf.tools.component_inventory_reader import ComponentInventoryReader
    from daf.tools.quality_report_parser import QualityReportParser
    from daf.tools.prose_generator import ProseGenerator

    agent = create_release_changelog_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    tool_types = [type(t) for t in agent.tools]
    assert ComponentInventoryReader in tool_types
    assert QualityReportParser in tool_types
    assert ProseGenerator in tool_types
