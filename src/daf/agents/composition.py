"""Composition Agent (Agent 18, Component Factory Crew).

Checks TSX component files for primitive-only composition, nesting depth,
and token compliance. Writes a composition audit and optional rejection.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.tools.composition_rule_engine import check_composition, compute_token_compliance
from daf.tools.nesting_validator import validate_nesting
from daf.tools.primitive_registry import get_all_primitives


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def run_composition_check(output_dir: str) -> dict[str, Any]:
    """Check composition rules for all TSX components in *output_dir*.

    Reads:
        ``{output_dir}/src/components/*.tsx``

    Writes:
        ``{output_dir}/reports/composition-audit.json``
        ``{output_dir}/reports/composition-rejection.json`` (only on violations)

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        A dict with per-component composition results.
    """
    od = Path(output_dir)
    src_dir = od / "src" / "components"
    reports_dir = od / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    registry = get_all_primitives()

    components: dict[str, Any] = {}
    violations: list[dict[str, Any]] = []

    tsx_files = sorted(src_dir.glob("*.tsx")) if src_dir.exists() else []
    # Exclude *.test.tsx and *.stories.tsx
    tsx_files = [f for f in tsx_files if ".test." not in f.name and ".stories." not in f.name]

    for tsx_file in tsx_files:
        name = tsx_file.stem
        source = tsx_file.read_text(encoding="utf-8")

        comp_result = check_composition(source, registry)
        nesting_result = validate_nesting(source)
        token_result = compute_token_compliance(source)

        composition_valid: bool = comp_result["valid"] and not nesting_result["forbidden_nesting"]
        depth = nesting_result.get("depth", 0)
        composition_depth_score = max(0.0, 1.0 - max(0, depth - 5) / 5)
        token_compliance: float = token_result.get("token_compliance", 1.0)

        component_violations: list[dict[str, Any]] = []
        if not comp_result["valid"]:
            for v in comp_result.get("violations", []):
                component_violations.append(v)
        if nesting_result["forbidden_nesting"]:
            for fn in nesting_result["forbidden_nesting"]:
                component_violations.append({"type": "forbidden_nesting", "detail": fn})
        if nesting_result.get("depth_warning"):
            component_violations.append({"type": "excessive_depth", "depth": depth})

        components[name] = {
            "composition_valid": composition_valid,
            "violations": component_violations,
            "non_primitive_imports": comp_result.get("non_primitive_imports", []),
            "composition_depth_score": composition_depth_score,
            "token_compliance": token_compliance,
            "depth": depth,
        }

        if component_violations:
            violations.append({"component": name, "violations": component_violations})

    audit: dict[str, Any] = {"components": components}
    (reports_dir / "composition-audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )

    if violations:
        rejection: dict[str, Any] = {"violations": violations}
        (reports_dir / "composition-rejection.json").write_text(
            json.dumps(rejection, indent=2), encoding="utf-8"
        )
        _call_llm(f"Composition check found {len(violations)} violation(s).")
    else:
        _call_llm("Composition check complete — all components passed.")

    return audit
