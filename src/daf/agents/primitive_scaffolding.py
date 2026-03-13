"""Primitive Scaffolding Agent (Agent 3, DS Bootstrap Crew).

Generates canonical specs/*.spec.yaml files for all 9 composition primitives
(plus ThemeProvider) by running the deterministic PrimitiveSpecGenerator tool
via Task T3.
"""
from __future__ import annotations

import os
from typing import Any

from crewai import Agent, Task

from daf.tools.primitive_spec_generator import PrimitiveSpecGenerator


def create_primitive_scaffolding_agent() -> Agent:
    """Instantiate the Primitive Scaffolding Agent (Tier 3 — Haiku)."""
    model = os.environ.get("DAF_TIER3_MODEL", "claude-3-haiku-20240307")
    return Agent(
        role="Primitive Scaffolding Agent",
        goal=(
            "Generate canonical spec YAML files for all 11 composition primitives "
            "(Box, Stack, HStack, VStack, Grid, Text, Icon, Pressable, Divider, Spacer, "
            "ThemeProvider) by invoking the PrimitiveSpecGenerator tool. "
            "Write all files to specs/ in the given output directory. "
            "Return a summary confirming the number of files written and their location."
        ),
        backstory=(
            "You are a design system scaffolding specialist responsible for authoring "
            "the primitive contract layer — the canonical YAML specs that define "
            "every composition primitive's props, token bindings, composition rules, "
            "and accessibility requirements. Your output is the source of truth for "
            "the Design-to-Code Crew (Phase 3) and the Component Factory Crew. "
            "All specs must be deterministic, token-bound, and structurally complete "
            "before any code generation can begin."
        ),
        tools=[PrimitiveSpecGenerator()],
        llm=model,
        verbose=False,
    )


def create_primitive_scaffolding_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T3: generate all 11 primitive spec YAMLs.

    Args:
        output_dir: Base directory under which specs/ will be created.
        context_tasks: Optional list of upstream Task objects (e.g. [task_t2]).
    """
    description = (
        f"Run Task T3: Primitive Scaffolding.\n\n"
        f"Invoke the PrimitiveSpecGenerator tool with:\n"
        f"  output_dir = '{output_dir}'\n\n"
        f"The tool will write 11 spec YAML files to {output_dir}/specs/:\n"
        f"  Box.spec.yaml, Stack.spec.yaml, HStack.spec.yaml, VStack.spec.yaml,\n"
        f"  Grid.spec.yaml, Text.spec.yaml, Icon.spec.yaml, Pressable.spec.yaml,\n"
        f"  Divider.spec.yaml, Spacer.spec.yaml, ThemeProvider.spec.yaml\n\n"
        f"RETURN the tool output string confirming:\n"
        f"  - Number of files generated\n"
        f"  - Absolute path to the specs/ directory"
    )

    task_kwargs: dict[str, Any] = dict(
        description=description,
        expected_output=(
            "A confirmation string in the format: "
            "'Generated 11 primitive specs in <absolute_path_to_specs_dir>'"
        ),
    )
    if context_tasks:
        task_kwargs["context"] = context_tasks

    return Task(**task_kwargs)
