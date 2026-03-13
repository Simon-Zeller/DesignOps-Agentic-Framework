"""Scope Classification Agent (Agent 12, Design-to-Code Crew).

Analyses spec files to classify the generation workload and builds a prioritised
generation queue (primitives → simple → complex).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.scope_analyzer import classify_component
from daf.tools.dependency_graph_builder import build_dependency_graph, topological_sort
from daf.tools.priority_queue_builder import build_priority_queue
from daf.tools.spec_parser import parse_spec


def _classify_specs(output_dir: str) -> None:
    """Discover, classify, and prioritise all component specs.

    Reads ``<output_dir>/specs/**/*.spec.yaml``, classifies each component,
    resolves dependency order, and writes ``<output_dir>/scope_classifier_output.json``.

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    specs_dir = od / "specs"

    # Discover all spec files
    spec_files = list(specs_dir.glob("**/*.spec.yaml")) if specs_dir.exists() else []

    raw_specs: dict[str, dict[str, Any]] = {}
    for spec_file in spec_files:
        parsed = parse_spec(str(spec_file))
        if parsed and "component" in parsed:
            raw_specs[parsed["component"]] = parsed

    if not raw_specs:
        # Nothing to classify — write empty output
        output = {"components": []}
        (od / "scope_classifier_output.json").write_text(
            json.dumps(output, indent=2), encoding="utf-8"
        )
        return

    # Classify each component
    classified: list[dict[str, Any]] = []
    for name, spec in raw_specs.items():
        tier = classify_component(spec)
        classified.append({"name": name, "tier": tier})

    # Build dependency graph and topological order
    graph = build_dependency_graph(raw_specs)
    topo_order = topological_sort(graph)

    # Build priority queue
    queue = build_priority_queue(classified, topo_order)

    output: dict[str, Any] = {"components": queue}
    (od / "scope_classifier_output.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )


def create_scope_classification_agent() -> Agent:
    """Instantiate the Scope Classification Agent (Agent 12 — Tier 3, Haiku)."""
    model = os.environ.get("DAF_TIER3_MODEL", "claude-haiku-4-20250514")
    return Agent(
        role="Component Scope Classifier",
        goal=(
            "Analyse all component spec files to classify the generation workload into "
            "primitives, simple components, and complex components. Produce a prioritised "
            "generation queue (primitives first) stored as scope_classifier_output.json."
        ),
        backstory=(
            "You are a design system architect with deep knowledge of component hierarchies. "
            "You quickly assess specs to determine generation complexity and ordering, "
            "ensuring the Code Generation Agent works in dependency-safe order."
        ),
        tools=[],
        llm=model,
        verbose=False,
    )


def create_scope_classification_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T1: Classify and prioritise component specs."""
    return Task(
        description=(
            f"Analyse all spec files in '{output_dir}/specs/**/*.spec.yaml'. "
            "Classify each component as primitive, simple, or complex. "
            "Resolve inter-component dependencies and produce a prioritised generation queue. "
            f"Write the result to '{output_dir}/scope_classifier_output.json'."
        ),
        expected_output=(
            "scope_classifier_output.json written with a 'components' list ordered "
            "primitive → simple → complex, respecting dependency order."
        ),
        agent=create_scope_classification_agent(),
        context=context_tasks or [],
    )
