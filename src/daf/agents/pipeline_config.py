"""Pipeline Configuration Agent (Agent 5, DS Bootstrap Crew).

Coordinates ConfigGenerator and ProjectScaffolder tools via Task T5 to produce
all four pipeline configuration files:
  - pipeline-config.json   (via ConfigGenerator)
  - tsconfig.json          (via ProjectScaffolder)
  - vitest.config.ts       (via ProjectScaffolder)
  - vite.config.ts         (via ProjectScaffolder)
"""
from __future__ import annotations

import os
from typing import Any

from crewai import Agent, Task

from daf.tools.config_generator import ConfigGenerator
from daf.tools.project_scaffolder import ProjectScaffolder


def create_pipeline_config_agent() -> Agent:
    """Instantiate the Pipeline Configuration Agent (Tier 2 — Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Pipeline Configuration Agent",
        goal=(
            "Generate pipeline-config.json and project scaffolding files "
            "(tsconfig.json, vitest.config.ts, vite.config.ts) by invoking "
            "ConfigGenerator first, then ProjectScaffolder, both with the validated "
            "Brand Profile and the designated output directory. "
            "Return a summary confirming all four files written and their locations."
        ),
        backstory=(
            "You are a design system infrastructure expert responsible for authoring "
            "the DS Bootstrap Crew's pipeline configuration layer. "
            "Your pipeline-config.json seeds the Governance Crew (Phase 4b) and your "
            "scaffolding files establish the TypeScript project structure consumed by "
            "the Design-to-Code Crew (Phase 3) and Component Factory Crew. "
            "All output is derived deterministically from the validated Brand Profile — "
            "you coordinate tool invocations and validate completeness of the output."
        ),
        tools=[ConfigGenerator(), ProjectScaffolder()],
        llm=model,
        verbose=False,
    )


def create_pipeline_config_task(
    output_dir: str = ".",
    brand_profile_path: str = "./brand-profile.json",
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T5: generate pipeline-config.json and project scaffolding files.

    Args:
        output_dir: Directory where all four output files will be written.
        brand_profile_path: Absolute or relative path to the validated brand-profile.json.
        context_tasks: Optional list of upstream Task objects (e.g. [task_t1]).
    """
    description = (
        f"Run Task T5: Pipeline Configuration.\n\n"
        f"Step 1: Read the validated brand-profile.json from '{brand_profile_path}'.\n"
        f"        Parse the JSON into a brand_profile_json string.\n\n"
        f"Step 2: Invoke ConfigGenerator with:\n"
        f"  brand_profile_json = <contents of brand-profile.json as JSON string>\n"
        f"  output_dir = '{output_dir}'\n\n"
        f"        Confirm the returned path exists before proceeding.\n\n"
        f"Step 3: Invoke ProjectScaffolder with:\n"
        f"  brand_profile_json = <same brand_profile_json as above>\n"
        f"  output_dir = '{output_dir}'\n\n"
        f"        Note: ConfigGenerator MUST run before ProjectScaffolder because\n"
        f"        ProjectScaffolder reads pipeline-config.json from output_dir.\n\n"
        f"Step 4: RETURN a confirmation listing all four output files and their paths:\n"
        f"  - pipeline-config.json\n"
        f"  - tsconfig.json\n"
        f"  - vitest.config.ts\n"
        f"  - vite.config.ts"
    )

    task_kwargs: dict[str, Any] = dict(
        description=description,
        expected_output=(
            "A confirmation listing all four output files written to "
            f"'{output_dir}': pipeline-config.json, tsconfig.json, "
            "vitest.config.ts, vite.config.ts — each with its absolute path."
        ),
    )
    if context_tasks:
        task_kwargs["context"] = context_tasks

    return Task(**task_kwargs)
