"""Render Validation Agent (Agent 15, Design-to-Code Crew).

Renders each generated component headlessly via Playwright and validates output.
Falls back to render_available=False when Playwright is unavailable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.playwright_renderer import check_renderer_available, render_component
from daf.tools.render_error_detector import detect_render_errors
from daf.tools.dimension_validator import validate_dimensions


def _validate_renders(output_dir: str) -> None:
    """Validate rendered output for all generated components.

    Discovers generated TSX files under ``src/``, renders each one (if Playwright
    is available), and writes ``render_validation_output.json``.

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    render_available = check_renderer_available()

    results: list[dict[str, Any]] = []

    # Discover generated component directories
    src_dir = od / "src"
    component_dirs: list[Path] = []
    for subdir in ("primitives", "components"):
        base = src_dir / subdir
        if base.exists():
            component_dirs.extend(
                d for d in base.iterdir() if d.is_dir()
            )

    for comp_dir in component_dirs:
        comp_name = comp_dir.name
        tsx_files = list(comp_dir.glob("*.tsx"))
        # Skip test and story files
        source_files = [f for f in tsx_files if not f.name.endswith((".test.tsx", ".stories.tsx"))]

        if not source_files:
            continue

        if not render_available:
            results.append({
                "component": comp_name,
                "render_pass": False,
                "render_available": False,
                "errors": [],
                "screenshots": [],
                "variants_checked": [],
            })
            continue

        # Load intent manifests to get variants
        manifests_path = od / "intent_manifests.json"
        variants: list[str] = ["default"]
        if manifests_path.exists():
            all_manifests = json.loads(manifests_path.read_text(encoding="utf-8"))
            for m in all_manifests:
                if m.get("component_name") == comp_name:
                    variants = m.get("variants") or ["default"]
                    break

        render_results: list[dict[str, Any]] = []
        all_pass = True

        for variant in variants:
            render_out = render_component(comp_name, variant, output_dir)
            errors = detect_render_errors(" ".join(render_out.get("render_errors", [])))
            dim_check = validate_dimensions(
                {"width": render_out.get("width", 0), "height": render_out.get("height", 0)}
            )

            variant_pass = not errors and dim_check["passed"]
            all_pass = all_pass and variant_pass

            render_results.append({
                "variant": variant,
                "path": render_out.get("path", ""),
                "passed": variant_pass,
                "errors": errors,
                "dimension_check": dim_check,
            })

        results.append({
            "component": comp_name,
            "render_pass": all_pass,
            "render_available": True,
            "errors": [e for r in render_results for e in r.get("errors", [])],
            "screenshots": [r["path"] for r in render_results if r.get("path")],
            "variants_checked": render_results,
        })

    output: dict[str, Any] = {
        "render_available": render_available,
        "results": results,
    }
    (od / "render_validation_output.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )


def create_render_validation_agent() -> Agent:
    """Instantiate the Render Validation Agent (Agent 15 — Tier 3, Haiku)."""
    model = os.environ.get("DAF_TIER3_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Render Validation Specialist",
        goal=(
            "Render each generated component headlessly via Playwright. Validate non-empty "
            "visual output per variant, check for render errors and React exceptions, "
            "and capture baseline screenshots to screenshots/. "
            "Fall back gracefully when Playwright is unavailable."
        ),
        backstory=(
            "You are a frontend quality engineer who validates component rendering in "
            "headless environments. You ensure generated components actually render correctly "
            "and capture baseline screenshots for downstream visual regression testing."
        ),
        tools=[],
        llm=model,
        verbose=False,
    )


def create_render_validation_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T4: Validate rendered component output."""
    return Task(
        description=(
            f"For each generated component under '{output_dir}/src/', render every declared variant "
            "headlessly via Playwright. Check for render errors, React exceptions, and zero-size output. "
            "Capture baseline screenshots to screenshots/<ComponentName>/. "
            f"Write results to '{output_dir}/render_validation_output.json'. "
            "If Playwright is unavailable, set render_available=False and continue."
        ),
        expected_output=(
            "render_validation_output.json written with render_available flag, "
            "per-component pass/fail results, error lists, and screenshot paths."
        ),
        agent=create_render_validation_agent(),
        context=context_tasks or [],
    )
