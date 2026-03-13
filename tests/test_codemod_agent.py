"""Tests for Agent 38 – Codemod Agent (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import crewai


def test_create_codemod_agent_returns_crewai_agent(tmp_path: Path) -> None:
    """Factory returns a crewai.Agent instance."""
    from daf.agents.codemod import create_codemod_agent

    agent = create_codemod_agent("claude-3-haiku-20240307", str(tmp_path))
    assert isinstance(agent, crewai.Agent)


def test_codemod_agent_role_keyword(tmp_path: Path) -> None:
    """Agent role contains 'codemod' or 'adoption' keyword."""
    from daf.agents.codemod import create_codemod_agent

    agent = create_codemod_agent("claude-3-haiku-20240307", str(tmp_path))
    role_lower = agent.role.lower()
    assert "codemod" in role_lower or "adoption" in role_lower or "helper" in role_lower


def test_codemod_agent_uses_haiku_model(tmp_path: Path) -> None:
    """Agent uses provided Haiku model string."""
    from daf.agents.codemod import create_codemod_agent

    model = "claude-3-haiku-20240307"
    agent = create_codemod_agent(model, str(tmp_path))
    assert agent.llm == model


def test_codemod_agent_has_required_tools(tmp_path: Path) -> None:
    """Agent tools include ASTPatternMatcher, CodemodTemplateGenerator, ExampleSuiteBuilder."""
    from daf.agents.codemod import create_codemod_agent
    from daf.tools.ast_pattern_matcher import ASTPatternMatcher
    from daf.tools.codemod_template_generator import CodemodTemplateGenerator
    from daf.tools.example_suite_builder import ExampleSuiteBuilder

    agent = create_codemod_agent("claude-3-haiku-20240307", str(tmp_path))
    tool_types = [type(t) for t in agent.tools]
    assert ASTPatternMatcher in tool_types
    assert CodemodTemplateGenerator in tool_types
    assert ExampleSuiteBuilder in tool_types
