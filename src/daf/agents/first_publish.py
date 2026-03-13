"""First Publish Agent (Agent 6, DS Bootstrap Crew).

Orchestrates the full 8-crew downstream pipeline with bounded retry routing,
phase-boundary checkpoints, and a final ResultAggregator call.

Architecture decisions (from design.md):
- Agent 6 holds a Python reference to Agent 40's CheckpointManager tool.
- Cross-phase retry (Phase 2 rejects Phase 1): restore checkpoint → re-run
  run_token_foundation_task with accumulated rejection context → re-run crew.
- Phases 1–3: up to MAX_PHASE13_RETRIES (3) per rejection boundary.
- Phases 4–6: up to MAX_PHASE46_RETRIES (2) per crew failure.
- CrewSequencer is used as a convenience utility for the happy path;
  Agent 6 uses its own orchestration loop for retry logic.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from crewai import Agent

from daf.agents.rollback import create_rollback_agent
from daf.agents.token_foundation import run_token_foundation_task
from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew
from daf.crews.analytics import create_analytics_crew
from daf.crews.component_factory import create_component_factory_crew
from daf.crews.design_to_code import create_design_to_code_crew
from daf.crews.documentation import create_documentation_crew
from daf.crews.governance import create_governance_crew
from daf.crews.release import create_release_crew
from daf.crews.token_engine import create_token_engine_crew
from daf.tools.checkpoint_manager import CheckpointManager
from daf.tools.crew_sequencer import (  # noqa: F401 (CrewSequencer imported for monkeypatching in tests)
    CrewResult,
    CrewSequencer,
)
from daf.tools.result_aggregator import ResultAggregator
from daf.tools.status_reporter import StatusReporter

MAX_PHASE13_RETRIES = 3   # Token Engine can be rejected up to 3 times
MAX_PHASE46_RETRIES = 2   # Phases 4–6 crews get 2 attempts

# Phase numbers for retry-category logic
_CRITICAL_PHASE_CREWS = {"token_engine", "design_to_code", "component_factory"}

_HAIKU_MODEL = "claude-3-5-haiku-20241022"

def create_first_publish_agent() -> Agent:
    """Instantiate Agent 6: First Publish Agent (Tier 2 — Claude Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-20250514")
    return Agent(
        role="First Publish Orchestrator",
        goal=(
            "Run the full 8-crew downstream pipeline in the correct phase order, "
            "handle cross-phase validation rejections with bounded retries, "
            "and produce a final generation-summary.json that the CLI can present "
            "to the user at Gate 2."
        ),
        backstory=(
            "You are the senior automated publisher for a design system generation platform. "
            "You coordinate 8 specialised AI crews — from token compilation to semantic layer — "
            "ensuring each phase completes before the next begins. When a validation crew rejects "
            "earlier output, you manage the rollback and retry loop without losing work. "
            "You deliver structured, machine-readable results for every pipeline run."
        ),
        tools=[
            CheckpointManager(),
            ResultAggregator(),
            StatusReporter(),
        ],
        llm=model,
        verbose=False,
    )


def run_first_publish_agent(
    output_dir: str,
    start_phase: int = 1,
    brand_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the downstream pipeline and return the generation summary dict.

    Args:
        output_dir: The design system output directory.
        start_phase: Which pipeline phase to start from (1 = full run, >1 = resume).
        brand_profile: Raw brand profile dict (needed for Phase 1–2 retry calls).

    Returns:
        The generation-summary dict written to ``reports/generation-summary.json``.
    """
    od = Path(output_dir)

    # Load brand_profile from disk if not supplied by caller
    if brand_profile is None:
        bp_path = od / "brand-profile.json"
        if bp_path.exists():
            brand_profile = json.loads(bp_path.read_text())

    cm = CheckpointManager()
    reporter = StatusReporter()
    aggregator = ResultAggregator()

    # Agent 40 must be instantiated before the first crew runs (per design.md)
    _rollback_agent = create_rollback_agent(_HAIKU_MODEL, output_dir)

    results: list[CrewResult] = []

    # Phase 1: Token Engine (Phases 1–3, with cross-phase retry support)
    if start_phase <= 1:
        te_result = _run_phase13_crew(
            crew_name="token_engine",
            factory=create_token_engine_crew,
            output_dir=output_dir,
            cm=cm,
            brand_profile=brand_profile,
            reporter=reporter,
            pre_checkpoint_phase=0,
        )
        results.append(te_result)
    else:
        results.append(CrewResult(crew="token_engine", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Phase 2: Design-to-Code
    if start_phase <= 2:
        d2c_result = _run_simple_crew(
            crew_name="design_to_code",
            factory=create_design_to_code_crew,
            output_dir=output_dir,
            reporter=reporter,
        )
        results.append(d2c_result)
    else:
        results.append(CrewResult(crew="design_to_code", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Phase 2 (continued): Component Factory
    if start_phase <= 2:
        cf_result = _run_simple_crew(
            crew_name="component_factory",
            factory=create_component_factory_crew,
            output_dir=output_dir,
            reporter=reporter,
        )
        results.append(cf_result)
        # Phase 3 checkpoint
        cm.create(output_dir=output_dir, phase=3)
    else:
        results.append(CrewResult(crew="component_factory", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Phase 4: Documentation then Governance (order enforced)
    if start_phase <= 4:
        doc_result = _run_with_retry(
            crew_name="documentation",
            factory=create_documentation_crew,
            output_dir=output_dir,
            max_retries=MAX_PHASE46_RETRIES,
            reporter=reporter,
        )
        results.append(doc_result)

        gov_result = _run_with_retry(
            crew_name="governance",
            factory=create_governance_crew,
            output_dir=output_dir,
            max_retries=MAX_PHASE46_RETRIES,
            reporter=reporter,
        )
        results.append(gov_result)
        # Phase 4 checkpoint
        cm.create(output_dir=output_dir, phase=4)
    else:
        results.append(CrewResult(crew="documentation", status="skipped", reason=f"resuming from phase {start_phase}"))
        results.append(CrewResult(crew="governance", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Phase 5: AI Semantic Layer + Analytics
    if start_phase <= 5:
        ai_result = _run_with_retry(
            crew_name="ai_semantic_layer",
            factory=create_ai_semantic_layer_crew,
            output_dir=output_dir,
            max_retries=MAX_PHASE46_RETRIES,
            reporter=reporter,
        )
        results.append(ai_result)

        analytics_result = _run_with_retry(
            crew_name="analytics",
            factory=create_analytics_crew,
            output_dir=output_dir,
            max_retries=MAX_PHASE46_RETRIES,
            reporter=reporter,
        )
        results.append(analytics_result)
        # Phase 5 checkpoint
        cm.create(output_dir=output_dir, phase=5)
    else:
        results.append(CrewResult(crew="ai_semantic_layer", status="skipped", reason=f"resuming from phase {start_phase}"))
        results.append(CrewResult(crew="analytics", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Phase 6: Release
    if start_phase <= 6:
        release_result = _run_with_retry(
            crew_name="release",
            factory=create_release_crew,
            output_dir=output_dir,
            max_retries=MAX_PHASE46_RETRIES,
            reporter=reporter,
        )
        results.append(release_result)
    else:
        results.append(CrewResult(crew="release", status="skipped", reason=f"resuming from phase {start_phase}"))

    # Remove skipped results before aggregation
    real_results = [r for r in results if r.status != "skipped"]
    if not real_results:
        real_results = results  # fallback: include skipped if nothing else

    summary = aggregator.aggregate(crew_results=real_results, output_dir=output_dir)

    # Cleanup checkpoints on full success
    if summary.get("pipeline", {}).get("status") == "success":
        cm.cleanup(output_dir=output_dir)

    return summary


# ---------------------------------------------------------------------------
# Per-crew runner helpers
# ---------------------------------------------------------------------------

def _run_phase13_crew(
    crew_name: str,
    factory: Any,
    output_dir: str,
    cm: CheckpointManager,
    brand_profile: dict[str, Any] | None,
    reporter: StatusReporter,
    pre_checkpoint_phase: int,
) -> CrewResult:
    """Run a Phase 1–3 crew with cross-phase retry routing (Token Engine path)."""
    accumulated_rejections: list[dict[str, Any]] = []
    retries_used = 0

    # Create initial checkpoint before Phase 1
    cm.create(output_dir=output_dir, phase=pre_checkpoint_phase)

    for attempt in range(1, MAX_PHASE13_RETRIES + 1):
        reporter.phase_start(crew=crew_name, phase=1)
        crew = factory(output_dir=output_dir)
        raw_result = crew.kickoff()

        result = _normalise_result(raw_result, crew_name)

        if result.status == "success":
            result.retries_used = retries_used
            reporter.phase_complete(crew=crew_name, phase=1, status="success")
            return result

        if result.status == "rejected":
            rejection = result.rejection or {}
            accumulated_rejections.append(rejection)

            if attempt < MAX_PHASE13_RETRIES:
                retries_used += 1
                reporter.phase_retry(crew=crew_name, phase=1, attempt=attempt)
                # Restore the pre-Phase checkpoint
                cm.restore(output_dir=output_dir, phase=pre_checkpoint_phase)
                # Re-run origin task with accumulated context
                run_token_foundation_task(
                    brand_profile,
                    output_dir,
                    retry_context=list(accumulated_rejections),
                )
            else:
                reporter.phase_failure(crew=crew_name, phase=1, reason="retries_exhausted")
                return CrewResult(
                    crew=crew_name,
                    status="failed",
                    retries_used=retries_used,
                    retries_exhausted=True,
                    reason="retries_exhausted",
                )
        else:
            # Plain failure (non-rejection)
            reporter.phase_failure(crew=crew_name, phase=1, reason=result.reason or "crew_failed")
            return CrewResult(
                crew=crew_name,
                status="failed",
                retries_used=retries_used,
                retries_exhausted=False,
                reason=result.reason,
            )

    # Should not be reachable, but satisfy the type-checker
    return CrewResult(
        crew=crew_name,
        status="failed",
        retries_used=retries_used,
        retries_exhausted=True,
        reason="retries_exhausted",
    )


def _run_simple_crew(
    crew_name: str,
    factory: Any,
    output_dir: str,
    reporter: StatusReporter,
) -> CrewResult:
    """Run a Phase 2–3 crew once (no retry)."""
    reporter.phase_start(crew=crew_name, phase=2)
    crew = factory(output_dir=output_dir)
    raw_result = crew.kickoff()
    result = _normalise_result(raw_result, crew_name)
    reporter.phase_complete(crew=crew_name, phase=2, status=result.status)
    return result


def _run_with_retry(
    crew_name: str,
    factory: Any,
    output_dir: str,
    max_retries: int,
    reporter: StatusReporter,
) -> CrewResult:
    """Run a Phase 4–6 crew with a bounded retry (non-fatal on exhaustion)."""
    retries_used = 0
    for attempt in range(1, max_retries + 1):
        reporter.phase_start(crew=crew_name, phase=4)
        crew = factory(output_dir=output_dir)
        raw_result = crew.kickoff()
        result = _normalise_result(raw_result, crew_name)

        if result.status in ("success", "partial"):
            result.retries_used = retries_used
            reporter.phase_complete(crew=crew_name, phase=4, status=result.status)
            return result

        if attempt < max_retries:
            retries_used += 1
            reporter.phase_retry(crew=crew_name, phase=4, attempt=attempt)
        else:
            reporter.phase_failure(crew=crew_name, phase=4, reason="retries_exhausted")
            return CrewResult(
                crew=crew_name,
                status="failed",
                retries_used=retries_used,
                retries_exhausted=True,
                reason="retries_exhausted",
            )

    # Should not be reachable
    return CrewResult(crew=crew_name, status="failed", retries_used=retries_used)


def _normalise_result(raw: Any, crew_name: str) -> CrewResult:
    """Convert a raw kickoff() return value to a CrewResult."""
    if isinstance(raw, CrewResult):
        return raw
    # Stub crews return a string — treat as success
    return CrewResult(crew=crew_name, status="success", artifacts_written=[])
