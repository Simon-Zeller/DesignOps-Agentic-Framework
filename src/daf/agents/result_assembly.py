"""Result Assembly Agent (Agent 16, Design-to-Code Crew).

Assembles per-component generation results, computes confidence scores,
and writes reports/generation-summary.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from daf.tools.confidence_scorer import compute_confidence
from daf.tools.report_writer import write_generation_summary


def _assemble_results(output_dir: str) -> None:
    """Assemble per-component generation results and write the summary report.

    Reads ``intent_manifests.json`` and ``render_validation_output.json``,
    computes confidence scores, and writes ``reports/generation-summary.json``.

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)

    # Load intent manifests
    manifests_path = od / "intent_manifests.json"
    manifests: list[dict[str, Any]] = []
    if manifests_path.exists():
        manifests = json.loads(manifests_path.read_text(encoding="utf-8"))

    # Load render validation output
    render_path = od / "render_validation_output.json"
    render_data: dict[str, Any] = {"render_available": False, "results": []}
    if render_path.exists():
        render_data = json.loads(render_path.read_text(encoding="utf-8"))

    render_available = render_data.get("render_available", False)
    render_results: dict[str, dict[str, Any]] = {
        r["component"]: r for r in render_data.get("results", [])
    }

    results: list[dict[str, Any]] = []
    for manifest in manifests:
        name = manifest["component_name"]
        tier = manifest.get("tier", "simple")
        variants = manifest.get("variants") or []
        token_bindings = manifest.get("token_bindings", [])

        # Determine output directory used
        if tier == "primitive":
            comp_dir = od / "src" / "primitives" / name
        else:
            comp_dir = od / "src" / "components" / name

        # Check what files were written
        files_written: list[str] = []
        for suffix in (f"{name}.tsx", f"{name}.test.tsx", f"{name}.stories.tsx"):
            if (comp_dir / suffix).exists():
                files_written.append(str(comp_dir / suffix))

        # Compute confidence sub-scores
        spec_completeness = 1.0 if token_bindings or variants else 0.5
        lint_pass = 1.0 if files_written else 0.0
        variant_coverage = 1.0 if variants else 0.8
        compilation_pass = 1.0 if files_written else 0.0

        render_result = render_results.get(name, {})
        render_pass_score = 1.0 if render_result.get("render_pass", False) else 0.0

        confidence_input = {
            "spec_completeness": spec_completeness,
            "lint_pass": lint_pass,
            "variant_coverage": variant_coverage,
            "render_pass": render_pass_score,
            "compilation_pass": compilation_pass,
            "render_available": render_available,
        }
        confidence_raw = compute_confidence(confidence_input)
        confidence_score = confidence_raw if isinstance(confidence_raw, int) else confidence_raw["score"]

        results.append({
            "component": name,
            "tier": tier,
            "files_written": files_written,
            "confidence": confidence_score,
            "warnings": render_result.get("errors", []),
            "render_available": render_available,
        })

    write_generation_summary(results, output_dir)

    # Write barrel export files
    primitives = [r["component"] for r in results if r["tier"] == "primitive"]
    components = [r["component"] for r in results if r["tier"] != "primitive"]

    primitives_dir = od / "src" / "primitives"
    primitives_dir.mkdir(parents=True, exist_ok=True)
    prim_exports = "".join(f"export * from './{n}/{n}';\n" for n in primitives)
    (primitives_dir / "index.ts").write_text(prim_exports, encoding="utf-8")

    components_dir = od / "src" / "components"
    components_dir.mkdir(parents=True, exist_ok=True)
    comp_exports = "".join(f"export * from './{n}/{n}';\n" for n in components)
    (components_dir / "index.ts").write_text(comp_exports, encoding="utf-8")

    src_dir = od / "src"
    root_exports = "export * from './primitives';\nexport * from './components';\n"
    (src_dir / "index.ts").write_text(root_exports, encoding="utf-8")


def create_result_assembly_agent() -> Agent:
    """Instantiate the Result Assembly Agent (Agent 16 — Tier 3, Haiku)."""
    model = os.environ.get("DAF_TIER3_MODEL", "anthropic/claude-sonnet-4-20250514")
    return Agent(
        role="Generation Result Assembler",
        goal=(
            "Assemble the structured generation report per component covering files generated, "
            "confidence score, and warnings. Write reports/generation-summary.json for "
            "downstream crews including the Component Factory and Documentation Crew."
        ),
        backstory=(
            "You are a metrics and reporting specialist in design system pipelines. "
            "You aggregate output from all generation tasks into a structured report that "
            "enables downstream crews to know what was generated, the quality level, "
            "and where to find each generated file."
        ),
        tools=[],
        llm=model,
        verbose=False,
    )


def create_result_assembly_task(
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T5: Assemble generation results and write summary report."""
    return Task(
        description=(
            f"Read '{output_dir}/intent_manifests.json' and '{output_dir}/render_validation_output.json'. "
            "For each component, determine which files were written (tsx/test/stories), "
            "compute a confidence score, and record any render warnings. "
            f"Write the structured report to '{output_dir}/reports/generation-summary.json'."
        ),
        expected_output=(
            "reports/generation-summary.json written with total_components, generated, failed counts, "
            "and a components array with per-component detail including confidence scores."
        ),
        agent=create_result_assembly_agent(),
        context=context_tasks or [],
    )
