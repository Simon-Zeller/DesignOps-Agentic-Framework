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

        # a11y: try both field names (a11y from parse_spec, a11yRequirements from raw spec)
        a11y_spec = spec.get("a11y") or spec.get("a11yRequirements") or {}
        # If parsed spec stored a11yRequirements in metadata, check there too
        meta = spec.get("metadata") or {}
        if not a11y_spec:
            a11y_spec = meta.get("a11yRequirements") or {}
        aria = extract_a11y_attributes({"a11y": a11y_spec})

        # Build token bindings — handle both formats:
        # 1. "tokens" dict: {key: token_ref}
        # 2. "tokenBindings" list: [{prop: ..., $value: ...}]
        token_bindings: list[dict[str, str]] = []
        raw_tokens = spec.get("tokens") or {}
        if isinstance(raw_tokens, dict):
            for key, token_ref in raw_tokens.items():
                token_bindings.append({"key": key, "token": str(token_ref)})

        raw_bindings = spec.get("tokenBindings") or meta.get("tokenBindings") or []
        if isinstance(raw_bindings, list):
            for binding in raw_bindings:
                if isinstance(binding, dict):
                    prop = binding.get("prop", "")
                    val = binding.get("$value", "").strip("{}") if binding.get("$value") else ""
                    if prop and val:
                        token_bindings.append({"key": prop, "token": val})

        # Extract props from spec
        raw_props = spec.get("props") or meta.get("props") or {}
        props: list[dict[str, Any]] = []
        if isinstance(raw_props, dict):
            for prop_name, prop_meta in raw_props.items():
                if not isinstance(prop_meta, dict):
                    prop_meta = {}
                props.append({
                    "name": prop_name,
                    "type": prop_meta.get("type", "any"),
                    "required": bool(prop_meta.get("required", False)),
                    "default": prop_meta.get("default"),
                    "description": prop_meta.get("description", ""),
                })

        # Composition rules
        comp_rules = spec.get("compositionRules") or meta.get("compositionRules") or {}

        manifests.append({
            "component_name": name,
            "description": spec.get("description") or meta.get("description") or "",
            "tier": comp.get("tier", "simple"),
            "variants": spec.get("variants") or [],
            "states": spec.get("states") or [],
            "composedOf": spec.get("composedOf") or [],
            "token_bindings": token_bindings,
            "props": props,
            "layout": layout,
            "aria": aria,
            "compositionRules": comp_rules,
        })

    (od / "intent_manifests.json").write_text(
        json.dumps(manifests, indent=2), encoding="utf-8"
    )


def create_intent_extraction_agent() -> Agent:
    """Instantiate the Intent Extraction Agent (Agent 13 — Tier 2, Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "anthropic/claude-sonnet-4-20250514")
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
