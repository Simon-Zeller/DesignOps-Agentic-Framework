"""Agent 39 – Publish Agent (Release Crew, Phase 6).

Factory: create_publish_agent(model, output_dir) → crewai.Agent
Role: Package assembler and final validator
Model tier: Haiku
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.dependency_resolver import DependencyResolver
from daf.tools.package_json_generator import PackageJsonGenerator
from daf.tools.report_writer import ReportWriter
from daf.tools.test_result_parser import TestResultParser


def create_publish_agent(model: str, output_dir: str) -> Agent:
    """Agent 39 – Package Assembler and Final Validator (Release Crew, Phase 6)."""
    return Agent(
        role="Package assembler and final validator",
        goal=(
            "Assemble the final package.json with correct dependencies, peer dependencies, "
            "entry points, TypeScript config, and export maps using PackageJsonGenerator. "
            "Execute npm install, tsc --noEmit, and npm test via DependencyResolver. "
            "Parse results with TestResultParser and write the definitive final_status "
            "(success | partial | failed) to reports/generation-summary.json using ReportWriter."
        ),
        backstory=(
            "You are a meticulous package release engineer. You ensure every design system "
            "release has a properly assembled npm package manifest, all dependencies resolved, "
            "and TypeScript compilation verified. You record the final pipeline status faithfully."
        ),
        tools=[
            PackageJsonGenerator(output_dir=output_dir),
            DependencyResolver(output_dir=output_dir),
            TestResultParser(output_dir=output_dir),
            ReportWriter(),
        ],
        llm=model,
        verbose=False,
    )
