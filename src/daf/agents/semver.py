"""Agent 36 – Semver Agent (Release Crew, Phase 6).

Factory: create_semver_agent(model, output_dir) → crewai.Agent
Role: Version calculator
Model tier: Haiku
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.gate_status_reader import GateStatusReader
from daf.tools.version_calculator import VersionCalculator


def create_semver_agent(model: str, output_dir: str) -> Agent:
    """Agent 36 – Version Calculator (Release Crew, Phase 6)."""
    return Agent(
        role="Version calculator",
        goal=(
            "Read quality gate results from reports/governance/quality-gates.json, "
            "determine the correct semantic version using the VersionCalculator tool, "
            "and write the chosen version to reports/generation-summary.json."
        ),
        backstory=(
            "You are a precise semantic versioning specialist. You apply a deterministic "
            "rule: v1.0.0 when all Fatal quality gates pass, v0.x.0 when any fails. "
            "You always use the GateStatusReader tool to read gate data and "
            "VersionCalculator to derive the version string."
        ),
        tools=[
            GateStatusReader(output_dir=output_dir),
            VersionCalculator(output_dir=output_dir),
        ],
        llm=model,
        verbose=False,
    )
