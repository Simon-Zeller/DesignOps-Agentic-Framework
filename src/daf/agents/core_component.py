"""Core Component Agent (Agent 4, DS Bootstrap Crew).

Generates canonical specs/*.spec.yaml files for all core UI components
across the three scope tiers (Starter, Standard, Comprehensive) by
running the deterministic CoreComponentSpecGenerator tool via Task T4.
"""
from __future__ import annotations

import os
from typing import Any

from crewai import Agent, Task

from daf.tools.core_component_spec_generator import CoreComponentSpecGenerator


def create_core_component_agent() -> Agent:
    """Instantiate the Core Component Agent (Tier 2 — Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-20250514")
    return Agent(
        role="Core Component Agent",
        goal=(
            "Generate canonical spec YAML files for all core UI components "
            "in the requested scope tier (starter: 10, standard: 19, "
            "comprehensive: 26 components) by invoking the CoreComponentSpecGenerator tool. "
            "Write all files to specs/ in the given output directory. "
            "Return a summary confirming the number of files written and their location."
        ),
        backstory=(
            "You are a design system component specification expert responsible for "
            "authoring the component contract layer — the canonical YAML specs that "
            "define every core UI component's props, variants, states, token bindings, "
            "composition rules, and accessibility requirements. "
            "Your output is the source of truth for the Design-to-Code Crew (Phase 3) "
            "and the Component Factory Crew. All specs must be deterministic, "
            "token-bound, and structurally complete before any code generation begins."
        ),
        tools=[CoreComponentSpecGenerator()],
        llm=model,
        verbose=False,
    )


def create_core_component_task(
    output_dir: str = ".",
    scope: str = "starter",
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T4: generate all core component spec YAMLs.

    Args:
        output_dir: Base directory under which specs/ will be created.
        scope: Scope tier: 'starter', 'standard', or 'comprehensive'.
        context_tasks: Optional list of upstream Task objects (e.g. [task_t3]).
    """
    scope_counts = {"starter": 10, "standard": 19, "comprehensive": 26}
    count = scope_counts.get(scope, "N")

    description = (
        f"Run Task T4: Core Component Scaffolding.\n\n"
        f"Invoke the CoreComponentSpecGenerator tool with:\n"
        f"  scope = '{scope}'\n"
        f"  output_dir = '{output_dir}'\n"
        f"  component_overrides_json = '{{}}'\n\n"
        f"The tool will write {count} spec YAML files to {output_dir}/specs/.\n\n"
        f"RETURN the tool output string confirming:\n"
        f"  - Number of files generated\n"
        f"  - Absolute path to the specs/ directory"
    )

    task_kwargs: dict[str, Any] = dict(
        description=description,
        expected_output=(
            f"A confirmation string in the format: "
            f"'Generated {count} component specs in <absolute_path_to_specs_dir>'"
        ),
    )
    if context_tasks:
        task_kwargs["context"] = context_tasks

    return Task(**task_kwargs)
