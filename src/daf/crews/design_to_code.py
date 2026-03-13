"""Design-to-Code Crew — sequences Agents 12–16 to classify, extract, generate,
validate, and assemble component source code from spec YAML files.
"""
from __future__ import annotations

from daf.crews._stub import StubCrew
from daf.agents.scope_classification import _classify_specs
from daf.agents.intent_extraction import _extract_intents
from daf.agents.code_generation import _generate_code
from daf.agents.render_validation import _validate_renders
from daf.agents.result_assembly import _assemble_results


def create_design_to_code_crew(output_dir: str) -> StubCrew:
    """Return a Design-to-Code Crew that runs Agents 12–16 sequentially.

    Args:
        output_dir: Root directory for all pipeline I/O.

    The crew:
      T1 — Scope Classification: classifies and prioritises component specs.
      T2 — Intent Extraction: extracts structured manifests from each spec.
      T3 — Code Generation: generates TSX source, tests, and stories.
      T4 — Render Validation: validates headless rendering (Playwright fallback).
      T5 — Result Assembly: computes confidence scores and writes the summary report.
    """

    def _run() -> None:
        # T1 — Classify and prioritise specs
        _classify_specs(output_dir)

        # T2 — Extract intent manifests
        _extract_intents(output_dir)

        # T3 — Generate TSX source, tests, stories
        _generate_code(output_dir)

        # T4 — Render validation (Playwright or fallback)
        _validate_renders(output_dir)

        # T5 — Assemble results and write generation-summary.json
        _assemble_results(output_dir)

    return StubCrew(name="design_to_code", run_fn=_run)
