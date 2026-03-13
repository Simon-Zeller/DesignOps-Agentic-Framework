"""Breakage Correlation Agent (Agent 35, Analytics Crew).

Analyses test failures from the generation pipeline and the Release Crew,
walks the dependency graph, and classifies each failure as ``root-cause``
or ``downstream``. Writes ``reports/breakage-correlation.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.dependency_chain_walker import DependencyChainWalker


def create_breakage_correlation_agent(model: str, output_dir: str) -> Agent:
    """Create the Breakage Correlation Agent (Agent 35) for the Analytics Crew.

    Args:
        model: LLM model name (Sonnet tier required for causal graph reasoning).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Breakage Correlation and Root-Cause Analysis Specialist",
        goal=(
            "Given the set of components that failed tests or validation during this "
            "pipeline run, walk the component dependency graph to distinguish root-cause "
            "failures (components that broke independently) from downstream failures "
            "(components that broke because a dependency broke). Produce a breakage "
            "correlation report that enables the team to fix root causes first and "
            "avoid chasing cascading failures."
        ),
        backstory=(
            "You are a design-system reliability engineer with expertise in graph-based "
            "failure attribution. You understand that in a tightly-coupled component "
            "graph, a single root-cause failure can cascade into dozens of downstream "
            "test failures. By identifying the true root causes, you enable the team to "
            "focus their debugging effort efficiently."
        ),
        tools=[DependencyChainWalker()],
        llm=model,
        verbose=False,
    )
