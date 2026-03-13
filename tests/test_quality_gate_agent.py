"""Tests for Agent 30: Quality Gate Agent."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_quality_gate_agent_has_correct_tools(tmp_path):
    """Agent tools include GateEvaluator, ThresholdGate, ReportWriter, TestSuiteGenerator."""
    from daf.agents.quality_gate import create_quality_gate_agent
    from daf.tools.gate_evaluator import GateEvaluator
    from daf.tools.threshold_gate import ThresholdGate
    from daf.tools.report_writer import ReportWriter
    from daf.tools.test_suite_generator import TestSuiteGenerator

    agent = create_quality_gate_agent("claude-3-5-haiku-20241022", str(tmp_path))

    tool_types = {type(t) for t in agent.tools}
    assert GateEvaluator in tool_types
    assert ThresholdGate in tool_types
    assert ReportWriter in tool_types
    assert TestSuiteGenerator in tool_types


def test_quality_gate_agent_uses_haiku_model(tmp_path):
    """Agent is configured with a Haiku model tier."""
    from daf.agents.quality_gate import create_quality_gate_agent

    agent = create_quality_gate_agent("claude-3-5-haiku-20241022", str(tmp_path))
    assert "haiku" in agent.llm.model.lower()
