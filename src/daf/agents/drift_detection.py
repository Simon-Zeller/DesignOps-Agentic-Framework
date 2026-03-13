"""Drift Detection Agent (Agent 33, Analytics Crew).

Compares the canonical spec YAML against generated TSX props and Markdown
documentation, flags inconsistencies, auto-patches auto-fixable docs drift,
and writes ``reports/drift-report.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.doc_patcher import DocPatcher
from daf.tools.drift_reporter import DriftReporter
from daf.tools.structural_comparator import StructuralComparator


def create_drift_detection_agent(model: str, output_dir: str) -> Agent:
    """Create the Drift Detection Agent (Agent 33) for the Analytics Crew.

    Args:
        model: LLM model name (Sonnet tier required for authoritativeness reasoning).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Spec-to-Code-to-Docs Drift Detection Specialist",
        goal=(
            "Identify every inconsistency between the canonical component spec (YAML), "
            "the generated TSX implementation, and the Markdown documentation. "
            "For each inconsistency, determine whether it is auto-fixable (docs can be "
            "patched in place) or requires a Design-to-Code re-run. Apply all auto-fixable "
            "patches and report all non-fixable drift for downstream action."
        ),
        backstory=(
            "You are a design-system quality engineer specialising in spec-code-docs "
            "consistency. You treat the canonical spec as the single source of truth "
            "and apply the authoritativeness hierarchy (spec > code > docs) when "
            "resolving conflicts. You never modify generated TSX directly — only "
            "Markdown documentation can be patched in this phase."
        ),
        tools=[StructuralComparator(), DriftReporter(), DocPatcher()],
        llm=model,
        verbose=False,
    )
