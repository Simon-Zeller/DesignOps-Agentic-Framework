"""Tests for Agent 39 – Publish Agent (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import crewai


def test_create_publish_agent_returns_crewai_agent(tmp_path: Path) -> None:
    """Factory returns a crewai.Agent instance."""
    from daf.agents.publish import create_publish_agent

    agent = create_publish_agent("claude-3-haiku-20240307", str(tmp_path))
    assert isinstance(agent, crewai.Agent)


def test_publish_agent_role_keyword(tmp_path: Path) -> None:
    """Agent role contains 'publish' or 'package' keyword."""
    from daf.agents.publish import create_publish_agent

    agent = create_publish_agent("claude-3-haiku-20240307", str(tmp_path))
    role_lower = agent.role.lower()
    assert "publish" in role_lower or "package" in role_lower or "assembl" in role_lower


def test_publish_agent_uses_haiku_model(tmp_path: Path) -> None:
    """Agent uses provided Haiku model string."""
    from daf.agents.publish import create_publish_agent

    model = "claude-3-haiku-20240307"
    agent = create_publish_agent(model, str(tmp_path))
    assert agent.llm == model


def test_publish_agent_has_required_tools(tmp_path: Path) -> None:
    """Agent tools include PackageJsonGenerator, DependencyResolver, TestResultParser, ReportWriter."""
    from daf.agents.publish import create_publish_agent
    from daf.tools.package_json_generator import PackageJsonGenerator
    from daf.tools.dependency_resolver import DependencyResolver
    from daf.tools.test_result_parser import TestResultParser
    from daf.tools.report_writer import ReportWriter

    agent = create_publish_agent("claude-3-haiku-20240307", str(tmp_path))
    tool_types = [type(t) for t in agent.tools]
    assert PackageJsonGenerator in tool_types
    assert DependencyResolver in tool_types
    assert TestResultParser in tool_types
    assert ReportWriter in tool_types
