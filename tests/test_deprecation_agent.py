"""Tests for Agent 28: Deprecation Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_deprecation_agent_has_correct_tools(tmp_path):
    """Agent tools include all four deprecation-related tools."""
    from daf.agents.deprecation import create_deprecation_agent
    from daf.tools.lifecycle_tagger import LifecycleTagger
    from daf.tools.deprecation_policy_generator import DeprecationPolicyGenerator
    from daf.tools.stability_classifier import StabilityClassifier
    from daf.tools.deprecation_tagger import DeprecationTagger

    agent = create_deprecation_agent("claude-3-5-haiku-20241022", str(tmp_path))

    tool_types = {type(t) for t in agent.tools}
    assert LifecycleTagger in tool_types
    assert DeprecationPolicyGenerator in tool_types
    assert StabilityClassifier in tool_types
    assert DeprecationTagger in tool_types


def test_deprecation_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.deprecation import create_deprecation_agent

    agent = create_deprecation_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()
