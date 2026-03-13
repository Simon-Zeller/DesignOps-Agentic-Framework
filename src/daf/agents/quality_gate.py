"""Quality Gate Agent (Agent 30, Governance Crew).

Evaluates five quality gates per component, writes governance/quality-gates.json,
and generates the four project-level TypeScript test suites.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.gate_evaluator import GateEvaluator
from daf.tools.threshold_gate import ThresholdGate
from daf.tools.report_writer import ReportWriter
from daf.tools.test_suite_generator import TestSuiteGenerator


def create_quality_gate_agent(model: str, output_dir: str) -> Agent:
    """Create the Quality Gate Agent (Agent 30) for the Governance Crew.

    Args:
        model: LLM model name (should be a Haiku-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Quality Gate Enforcement Specialist",
        goal=(
            "Evaluate five independent quality gates per component, produce a "
            "comprehensive quality-gates.json report, and generate the four "
            "TypeScript test suites that encode exit criteria as executable tests."
        ),
        backstory=(
            "You are a quality engineering expert who ensures design system components "
            "meet rigorous standards for coverage, accessibility, documentation, and "
            "token compliance before they are considered production-ready."
        ),
        tools=[GateEvaluator(), ThresholdGate(), ReportWriter(), TestSuiteGenerator()],
        llm=model,
        verbose=False,
    )
