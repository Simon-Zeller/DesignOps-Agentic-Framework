"""Usage Tracking Agent (Agent 31, Analytics Crew).

Scans all generated TSX source for actual token usage, identifies dead and
phantom token references, and builds per-component import relationships.
Writes ``reports/usage-tracking.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.ast_import_scanner import ASTImportScanner
from daf.tools.token_usage_mapper import TokenUsageMapper


def create_usage_tracking_agent(model: str, output_dir: str) -> Agent:
    """Create the Usage Tracking Agent (Agent 31) for the Analytics Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Usage Tracking and Dependency Analysis Specialist",
        goal=(
            "Scan all generated TSX files to identify which design tokens are "
            "actively used, which are defined but never referenced (dead tokens), "
            "and which are referenced but undefined (phantom references). "
            "Produce a complete inter-component import graph and usage-tracking report."
        ),
        backstory=(
            "You are a design-system analyst specialising in token governance and "
            "dependency mapping. You ensure that every generated component correctly "
            "references design tokens and that the dependency graph is accurate, "
            "enabling the team to prune dead tokens and resolve phantom references."
        ),
        tools=[ASTImportScanner(), TokenUsageMapper()],
        llm=model,
        verbose=False,
    )
