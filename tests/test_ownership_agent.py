"""Tests for Agent 26: Ownership Agent."""
from __future__ import annotations


def test_ownership_agent_has_correct_role_and_tools(tmp_path):
    """Agent role contains 'ownership' and tools include the three expected classes."""
    from daf.agents.ownership import create_ownership_agent
    from daf.tools.domain_classifier import DomainClassifier
    from daf.tools.relationship_analyzer import RelationshipAnalyzer
    from daf.tools.orphan_scanner import OrphanScanner

    agent = create_ownership_agent("claude-3-5-sonnet-20241022", str(tmp_path))

    assert "ownership" in agent.role.lower()
    tool_types = {type(t) for t in agent.tools}
    assert DomainClassifier in tool_types
    assert RelationshipAnalyzer in tool_types
    assert OrphanScanner in tool_types


def test_ownership_agent_uses_sonnet_model(tmp_path):
    """Agent is configured with a Sonnet model tier."""
    from daf.agents.ownership import create_ownership_agent

    agent = create_ownership_agent("claude-3-5-sonnet-20241022", str(tmp_path))
    assert "sonnet" in agent.llm.model.lower()
