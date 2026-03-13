"""Intent Extraction Agent (Agent 13, Design-to-Code Crew).

For each component in the generation queue, extracts layout structure, spacing
model, token bindings, and a11y attributes. Writes intent_manifests.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.spec_parser import parse_spec
from daf.tools.layout_analyzer import extract_layout
from daf.tools.a11y_attribute_extractor import extract_a11y_attributes


def _extract_intents(output_dir: str) -> None:
    """Extract structured intent manifests for each queued component.

    Reads ``scope_classifier_output.json`` and each corresponding ``*.spec.yaml``,
    then writes ``intent_manifests.json``.

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)

    # Load scope classifier output
    scope_path = od / "scope_classifier_output.json"
    if not scope_path.exists():
        raise FileNotFoundError(
            f"scope_classifier_output.json not found in '{output_dir}'. "
            "Ensure Scope Classification Agent has completed."
        )

    scope_data = json.loads(scope_path.read_text(encoding="utf-8"))
    components: list[dict[str, Any]] = scope_data.get("components", [])

    # Build a name → spec file mapping
    spec_files: dict[str, Path] = {}
    specs_dir = od / "specs"
    if specs_dir.exists():
        for f in specs_dir.glob("**/*.spec.yaml"):
            parsed = parse_spec(str(f))
            if parsed and "component" in parsed:
                spec_files[parsed["component"]] = f

    manifests: list[dict[str, Any]] = []
    for comp in components:
        name = comp["name"]
        spec_file = spec_files.get(name)
        if spec_file:
            spec = parse_spec(str(spec_file)) or {}
        else:
            spec = {"component": name}

        layout = extract_layout(spec)
        aria = extract_a11y_attributes(spec)

        # Build token bindings from spec tokens field
        token_bindings: list[dict[str, str]] = []
        for key, token_ref in (spec.get("tokens") or {}).items():
            token_bindings.append({"key": key, "token": token_ref})

        manifests.append({
            "component_name": name,
            "tier": comp.get("tier", "simple"),
            "variants": spec.get("variants") or [],
            "states": spec.get("states") or [],
            "composedOf": spec.get("composedOf") or [],
            "token_bindings": token_bindings,
            "layout": layout,
            "aria": aria,
        })

    (od / "intent_manifests.json").write_text(
        json.dumps(manifests, indent=2), encoding="utf-8"
    )


def create_intent_extraction_agent() -> Agent:
    """Instantiate the Intent Extraction Agent (Agent 13 — Tier 2, Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-5")
    return Agent(
        role="Component Intent Extractor",
        goal=(
            "For each component in the generation queue, extract a structured intent manifest "
            "covering layout structure, token bindings, interactive states, slot definitions, "
            "and accessibility attribute requirements. Write intent_manifests.json."
        ),
        backstory=(
            "You are a senior frontend architect skilled in translating design spec language "
            "into precise implementation intent. You extract all structural and semantic meaning "
            "from specs to produce manifests that the Code Generation Agent can execute against."
        ),
        tools=[],
        llm=model,
        verbose=False,
    )


def create_intent_extraction_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T2: Extract intent manifests for all queued components."""
    return Task(
        description=(
            f"Read '{output_dir}/scope_classifier_output.json' and each referenced spec YAML. "
            "For each component, extract layout model, token bindings, variants, states, "
            "composedOf dependencies, and a11y attributes. "
            f"Write all manifests to '{output_dir}/intent_manifests.json'."
        ),
        expected_output=(
            "intent_manifests.json written with one manifest object per component, "
            "each containing component_name, layout, token_bindings, variants, states, "
            "composedOf, and aria keys."
        ),
        agent=create_intent_extraction_agent(),
        context=context_tasks or [],
    )
