"""Component Factory Crew (Agents 17–20).

Orchestrates the four-agent pipeline:
  17. Spec Validation  — validates YAML specs, token refs, state machines
  18. Composition      — checks TSX primitive-only composition and nesting
  19. Accessibility    — applies ARIA patches and keyboard scaffolding
  20. Quality Scoring  — aggregates sub-scores and applies the 70/100 gate
"""
from __future__ import annotations

from daf.crews._stub import StubCrew
from daf.agents.spec_validation import run_spec_validation
from daf.agents.composition import run_composition_check
from daf.agents.accessibility import run_accessibility_enforcement
from daf.agents.quality_scoring import run_quality_scoring


def create_component_factory_crew(output_dir: str) -> StubCrew:
    """Create the Component Factory Crew for *output_dir*.

    Returns a :class:`~daf.crews._stub.StubCrew` whose ``.kickoff()`` method
    runs all four agents sequentially.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        A crew object with a ``.kickoff()`` method.
    """

    def _run() -> None:
        run_spec_validation(output_dir)
        run_composition_check(output_dir)
        run_accessibility_enforcement(output_dir)
        run_quality_scoring(output_dir)

    return StubCrew(name="component_factory", run_fn=_run)
