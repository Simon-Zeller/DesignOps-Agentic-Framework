"""PipelineStageTracker — checks per-component presence across pipeline stages.

Stages (in order):
1. ``spec_validated``  — ``specs/<name>.spec.yaml`` exists
2. ``code_generated``  — ``src/components/<Name>.tsx`` exists
3. ``a11y_passed``     — ``reports/a11y-audit.json`` exists and has entry for component
4. ``tests_written``   — ``tests/<Name>.test.tsx`` exists
5. ``docs_generated``  — ``docs/components/<name>.md`` exists

Returns per-component ``{name, stages, completeness_score, stuck_at, intervention}``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_STAGE_ORDER = [
    "spec_validated",
    "code_generated",
    "a11y_passed",
    "tests_written",
    "docs_generated",
]

_INTERVENTIONS = {
    "code_generated": "Re-run the Design-to-Code Crew to generate TSX for this component.",
    "a11y_passed": "Re-run the Component Factory Crew to perform accessibility checks.",
    "tests_written": "Add a test file for this component under tests/.",
    "docs_generated": "Re-run the Documentation Crew to generate Markdown docs.",
}


def _check_stages(output_dir: str, component: str) -> dict[str, Any]:
    od = Path(output_dir)
    name_lower = component.lower()

    stages = {
        "spec_validated": (od / "specs" / f"{name_lower}.spec.yaml").exists(),
        "code_generated": (od / "src" / "components" / f"{component}.tsx").exists(),
        "a11y_passed": _check_a11y(od, component),
        "tests_written": (od / "tests" / f"{component}.test.tsx").exists(),
        "docs_generated": (od / "docs" / "components" / f"{name_lower}.md").exists(),
    }

    # First False stage = stuck_at
    stuck_at: str | None = None
    for stage in _STAGE_ORDER:
        if not stages[stage]:
            stuck_at = stage
            break

    completeness_score = round(sum(stages.values()) / len(_STAGE_ORDER), 4)
    intervention = _INTERVENTIONS.get(stuck_at, None) if stuck_at else None

    return {
        "name": component,
        "stages": stages,
        "completeness_score": completeness_score,
        "stuck_at": stuck_at,
        "intervention": intervention,
    }


def _check_a11y(od: Path, component: str) -> bool:
    a11y_path = od / "reports" / "a11y-audit.json"
    if not a11y_path.exists():
        return False
    try:
        import json
        data = json.loads(a11y_path.read_text(encoding="utf-8"))
        entry = data.get(component, {})
        return bool(entry.get("passed", False))
    except Exception:  # noqa: BLE001
        return False


def track_stages(output_dir: str, components: list[str]) -> dict[str, Any]:
    """Track pipeline stage completion for each component.

    Args:
        output_dir: Root pipeline output directory.
        components: List of component names to check.

    Returns:
        Dict with ``components`` key — list of per-component stage reports.
    """
    return {"components": [_check_stages(output_dir, c) for c in components]}


class _TrackerInput(BaseModel):
    output_dir: str
    components: list[str]


class PipelineStageTracker(BaseTool):
    """Track per-component pipeline stage completeness."""

    name: str = "pipeline_stage_tracker"
    description: str = (
        "For each component name, check presence of spec YAML, TSX, test, docs, and "
        "a11y report. Returns {components: [{name, stages, completeness_score, "
        "stuck_at, intervention}]}."
    )
    args_schema: type[BaseModel] = _TrackerInput

    def _run(
        self,
        output_dir: str,
        components: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return track_stages(output_dir, components)
