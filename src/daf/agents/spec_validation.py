"""Spec Validation Agent (Agent 17, Component Factory Crew).

Validates component spec YAML files against schema, token references, and
state machine correctness. Writes a validation report and an optional
rejection file for any specs with errors.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from daf.tools.token_ref_checker import check_token_refs
from daf.tools.state_machine_validator import validate_state_machine


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def run_spec_validation(output_dir: str) -> dict[str, Any]:
    """Validate all component specs in *output_dir* and write reports.

    Reads:
        ``{output_dir}/specs/*.spec.yaml``
        ``{output_dir}/tokens/semantic.tokens.json``

    Writes:
        ``{output_dir}/reports/spec-validation-report.json``
        ``{output_dir}/reports/spec-validation-rejection.json`` (only on failures)

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        A dict with keys ``components`` (per-component results) and
        ``summary`` (counts of valid/invalid specs).
    """
    od = Path(output_dir)
    specs_dir = od / "specs"
    reports_dir = od / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load compiled tokens (flat key → value)
    compiled_tokens: dict[str, str] = {}
    token_path = od / "tokens" / "semantic.tokens.json"
    if token_path.exists():
        compiled_tokens = json.loads(token_path.read_text(encoding="utf-8"))

    components: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []

    spec_files = sorted(specs_dir.glob("*.spec.yaml")) if specs_dir.exists() else []

    for spec_file in spec_files:
        try:
            spec: dict[str, Any] = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            name = spec_file.stem.replace(".spec", "").title()
            components[name] = {"valid": False, "errors": [str(exc)], "spec_completeness": 0.0}
            failures.append({"component": name, "reason": "yaml_parse_error", "detail": str(exc)})
            continue

        name: str = spec.get("component", spec_file.stem.replace(".spec", "").title())

        errors: list[str] = []

        # --- Token reference check ---
        spec_tokens: dict[str, str] = spec.get("tokens", {})
        if spec_tokens:
            token_result = check_token_refs(spec_tokens, compiled_tokens)
            for unresolved in token_result.get("unresolved", []):
                errors.append(f"unresolved_token: {unresolved}")

        # --- State machine check: only hard errors (terminal with outgoing transitions) ---
        states: dict[str, Any] = spec.get("states", {})
        if states:
            sm_result = validate_state_machine(states)
            for bad in sm_result.get("invalid_transitions", []):
                errors.append(f"invalid_transition: {bad}")

        # --- Spec completeness heuristic ---
        required_keys = {"component", "variants", "states", "tokens", "a11y"}
        present = required_keys & set(spec.keys())
        spec_completeness = len(present) / len(required_keys)

        valid = len(errors) == 0
        components[name] = {
            "valid": valid,
            "errors": errors,
            "spec_completeness": spec_completeness,
        }

        if not valid:
            failures.append({"component": name, "errors": errors})

    summary = {
        "total": len(components),
        "valid": sum(1 for c in components.values() if c["valid"]),
        "invalid": sum(1 for c in components.values() if not c["valid"]),
    }

    report: dict[str, Any] = {"components": components, "summary": summary}
    (reports_dir / "spec-validation-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    if failures:
        rejection: dict[str, Any] = {"failures": failures}
        (reports_dir / "spec-validation-rejection.json").write_text(
            json.dumps(rejection, indent=2), encoding="utf-8"
        )
        _call_llm(f"Spec validation found {len(failures)} failure(s): {failures}")
    else:
        _call_llm("Spec validation complete — all specs passed.")

    return report
