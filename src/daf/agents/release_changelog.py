"""Agent 37 – Release Changelog Agent (Release Crew, Phase 6).

Factory: create_release_changelog_agent(model, output_dir) → crewai.Agent
Role: Release inventory author
Model tier: Sonnet
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.component_inventory_reader import ComponentInventoryReader
from daf.tools.prose_generator import ProseGenerator
from daf.tools.quality_report_parser import QualityReportParser


def create_release_changelog_agent(model: str, output_dir: str) -> Agent:
    """Agent 37 – Release Inventory Author (Release Crew, Phase 6)."""
    return Agent(
        role="Release inventory author",
        goal=(
            "Read the component inventory and quality gate results, then write "
            "docs/changelog.md as structured prose grouped by category: full component "
            "inventory with status and quality score, token category summary, gate "
            "pass/fail summary, and known issues with failed components."
        ),
        backstory=(
            "You are an experienced technical writer specialising in design system "
            "release notes. You produce well-structured changelogs that are both human "
            "readable and machine parseable. You leverage ComponentInventoryReader and "
            "QualityReportParser for raw data and ProseGenerator for narrative composition."
        ),
        tools=[
            ComponentInventoryReader(output_dir=output_dir),
            QualityReportParser(output_dir=output_dir),
            ProseGenerator(output_dir=output_dir),
        ],
        llm=model,
        verbose=False,
    )
