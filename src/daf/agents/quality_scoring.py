"""Quality Scoring Agent (Agent 20, Component Factory Crew).

Aggregates results from spec validation, composition, and accessibility audits
plus test coverage data to compute a composite quality score for each component.
Applies the 70/100 quality gate and writes a scorecard and checkpoint.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.tools.score_calculator import calculate_score
from daf.tools.threshold_gate import apply_gate
from daf.tools.coverage_reporter import get_coverage


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def _collect_component_names(
    a11y: dict[str, Any],
    composition: dict[str, Any],
    spec: dict[str, Any],
    src_dir: Path,
) -> set[str]:
    """Union of component names across all audit sources."""
    names: set[str] = set()
    names.update(a11y.get("components", {}).keys())
    names.update(composition.get("components", {}).keys())
    names.update(spec.get("components", {}).keys())
    if src_dir.exists():
        for tsx in src_dir.glob("*.tsx"):
            if ".test." not in tsx.name and ".stories." not in tsx.name:
                names.add(tsx.stem)
    return names


def run_quality_scoring(output_dir: str) -> dict[str, Any]:
    """Compute composite quality scores for all components and apply the gate.

    Reads:
        ``{output_dir}/reports/a11y-audit.json``
        ``{output_dir}/reports/composition-audit.json``
        ``{output_dir}/reports/spec-validation-report.json``
        ``{output_dir}/coverage/lcov.json``

    Writes:
        ``{output_dir}/reports/quality-scorecard.json``
        ``{output_dir}/checkpoints/component-factory.json``

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        A dict with per-component scores and a ``summary`` section.
    """
    od = Path(output_dir)
    reports_dir = od / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = od / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # --- Load audit reports ---
    def _load_json(path: Path) -> dict[str, Any]:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    a11y_audit = _load_json(reports_dir / "a11y-audit.json")
    composition_audit = _load_json(reports_dir / "composition-audit.json")
    spec_audit = _load_json(reports_dir / "spec-validation-report.json")
    coverage_path = str(od / "coverage" / "lcov.json")
    src_dir = od / "src" / "components"

    all_names = _collect_component_names(a11y_audit, composition_audit, spec_audit, src_dir)

    components: dict[str, Any] = {}
    passed_count = 0
    failed_count = 0

    for name in sorted(all_names):
        a11y_comp = a11y_audit.get("components", {}).get(name, {})
        comp_comp = composition_audit.get("components", {}).get(name, {})
        spec_comp = spec_audit.get("components", {}).get(name, {})

        # Resolve coverage for this component
        tsx_filename = f"{name}.tsx"
        coverage_value = get_coverage(tsx_filename, coverage_path)

        # Build sub-scores dict
        sub_scores: dict[str, float] = {
            "a11y_pass_rate": float(a11y_comp.get("a11y_pass_rate", 0.0)),
            "composition_depth_score": float(comp_comp.get("composition_depth_score", 0.0)),
            "token_compliance": float(comp_comp.get("token_compliance", 0.0)),
            "spec_completeness": float(spec_comp.get("spec_completeness", 0.0)),
        }
        if coverage_value is not None:
            sub_scores["test_coverage"] = coverage_value

        score_result = calculate_score(sub_scores)
        composite: float = score_result["composite"]
        gate_result = apply_gate(composite)

        entry: dict[str, Any] = {
            "composite": composite,
            "gate": gate_result["gate"],
            "sub_scores": score_result["sub_scores"],
        }
        if score_result.get("coverage_unavailable"):
            entry["coverage_unavailable"] = True

        components[name] = entry

        if gate_result["verdict"]:
            passed_count += 1
        else:
            failed_count += 1

    summary = {
        "total": len(components),
        "passed": passed_count,
        "failed": failed_count,
    }

    scorecard: dict[str, Any] = {"components": components, "summary": summary}
    (reports_dir / "quality-scorecard.json").write_text(
        json.dumps(scorecard, indent=2), encoding="utf-8"
    )

    # Write checkpoint
    checkpoint: dict[str, Any] = {
        "agent": "component-factory",
        "summary": summary,
        "gate": "passed" if failed_count == 0 else "failed",
    }
    (checkpoints_dir / "component-factory.json").write_text(
        json.dumps(checkpoint, indent=2), encoding="utf-8"
    )

    _call_llm(f"Quality scoring complete: {passed_count} passed, {failed_count} failed.")
    return scorecard
