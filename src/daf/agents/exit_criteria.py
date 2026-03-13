"""Exit Criteria Agent (Agent 30-bis, Governance Crew, p19).

Thin agent wrapper over ExitCriteriaEvaluator and ReportWriter.
Uses Haiku-tier model — no LLM inference required, only tool invocation.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
from daf.tools.report_writer import ReportWriter


def create_exit_criteria_agent(model: str, output_dir: str) -> Agent:
    """Create the Exit Criteria Agent (Agent 30-bis) for the Governance Crew.

    Args:
        model: LLM model name (should be a Haiku-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Exit Criteria Evaluator",
        goal=(
            "Run all 15 §8 exit criteria checks against the pipeline output "
            "directory and write the structured report to reports/exit-criteria.json."
        ),
        backstory=(
            "You are a quality gate enforcer who deterministically evaluates "
            "whether a design system release meets all defined exit criteria "
            "before it is published."
        ),
        tools=[ExitCriteriaEvaluator(), ReportWriter()],
        llm=model,
        verbose=False,
    )
