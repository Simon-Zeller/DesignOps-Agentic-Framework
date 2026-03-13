"""Pipeline Completeness Agent (Agent 34, Analytics Crew).

Tracks each generated component's completeness across all pipeline stages
(spec → code → a11y → tests → docs) and writes
``reports/pipeline-completeness.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.pipeline_stage_tracker import PipelineStageTracker


def create_pipeline_completeness_agent(model: str, output_dir: str) -> Agent:
    """Create the Pipeline Completeness Agent (Agent 34) for the Analytics Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Pipeline Completeness and Stage Progression Analyst",
        goal=(
            "For every generated component, determine which pipeline stages have been "
            "successfully completed and which are outstanding. Identify components that "
            "are stuck at a specific stage and recommend the appropriate intervention "
            "to unblock progression. Produce a completeness report with per-component "
            "scores and interventions."
        ),
        backstory=(
            "You are a design-system pipeline monitor who tracks the progression of "
            "every component from spec through code generation, accessibility validation, "
            "test coverage, and documentation. You quickly identify bottlenecks and "
            "prescribe targeted remediation steps so no component falls behind."
        ),
        tools=[PipelineStageTracker()],
        llm=model,
        verbose=False,
    )
