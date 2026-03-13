"""Tests for Agent 29: RFC Agent."""
from __future__ import annotations


def test_rfc_agent_has_correct_tools(tmp_path):
    """Agent tools include RFCTemplateGenerator and ProcessDefinitionBuilder."""
    from daf.agents.rfc import create_rfc_agent
    from daf.tools.rfc_template_generator import RFCTemplateGenerator
    from daf.tools.process_definition_builder import ProcessDefinitionBuilder

    agent = create_rfc_agent("claude-3-5-haiku-20241022", str(tmp_path))

    tool_types = {type(t) for t in agent.tools}
    assert RFCTemplateGenerator in tool_types
    assert ProcessDefinitionBuilder in tool_types


def test_rfc_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.rfc import create_rfc_agent

    agent = create_rfc_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()
