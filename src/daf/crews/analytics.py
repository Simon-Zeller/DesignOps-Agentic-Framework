"""Analytics Crew (Agents 31–35, Phase 5).

Replaces the stub with a real CrewAI Crew housing five agents — Usage Tracking,
Token Compliance, Drift Detection, Pipeline Completeness, and Breakage
Correlation — running tasks T1–T5 in sequential order.

Pre-flight guard: raises ``RuntimeError`` if no ``*.spec.yaml`` files are found
in ``<output_dir>/specs/``, as Agents 31 and 33 require spec input.
"""
from __future__ import annotations

from pathlib import Path

from crewai import Crew, Task

from daf.agents.breakage_correlation import create_breakage_correlation_agent
from daf.agents.drift_detection import create_drift_detection_agent
from daf.agents.pipeline_completeness import create_pipeline_completeness_agent
from daf.agents.token_compliance_agent import create_token_compliance_agent
from daf.agents.usage_tracking import create_usage_tracking_agent

_SONNET_MODEL = "claude-3-5-sonnet-20241022"
_HAIKU_MODEL = "claude-3-5-haiku-20241022"


def create_analytics_crew(output_dir: str) -> Crew:
    """Create the Analytics Crew for *output_dir*.

    Pre-flight: verifies that ``specs/*.spec.yaml`` files exist.

    Args:
        output_dir: Root pipeline output directory.

    Raises:
        RuntimeError: If no ``specs/*.spec.yaml`` files are found.

    Returns:
        A :class:`crewai.Crew` with 5 tasks wired T1→T5.
    """
    od = Path(output_dir)
    spec_files = list((od / "specs").glob("*.spec.yaml")) if (od / "specs").exists() else []

    if not spec_files:
        raise RuntimeError(
            "Analytics Crew pre-flight failed — no specs/*.spec.yaml files found in "
            f"{od / 'specs'}. Ensure the Token Engine Crew has completed before Phase 5."
        )

    # Ensure reports directory exists
    (od / "reports").mkdir(parents=True, exist_ok=True)

    # Instantiate agents
    usage_agent = create_usage_tracking_agent(_HAIKU_MODEL, output_dir)
    compliance_agent = create_token_compliance_agent(_HAIKU_MODEL, output_dir)
    drift_agent = create_drift_detection_agent(_SONNET_MODEL, output_dir)
    completeness_agent = create_pipeline_completeness_agent(_HAIKU_MODEL, output_dir)
    breakage_agent = create_breakage_correlation_agent(_SONNET_MODEL, output_dir)

    # Define tasks T1–T5
    t1_usage = Task(
        description=(
            f"Scan all TSX files under {od / 'src'} for import relationships and "
            f"token usage patterns against token definitions in {od / 'tokens'}. "
            "Identify dead tokens (defined but unused) and phantom references "
            "(used but undefined). Write the report to reports/usage-tracking.json."
        ),
        expected_output=(
            "JSON file at reports/usage-tracking.json containing dead_tokens, "
            "phantom_refs, used_tokens arrays and the per-component import graph."
        ),
        agent=usage_agent,
    )

    t2_compliance = Task(
        description=(
            f"Scan all TSX files under {od / 'src'} for hardcoded colour, spacing, "
            "and font-size values. Report each violation with file path, value, type, "
            "and suggested replacement token. Compute overall compliance_score. "
            "Write the report to reports/token-compliance.json."
        ),
        expected_output=(
            "JSON file at reports/token-compliance.json with a violations array "
            "(each entry: file, value, type, suggested_token) and a summary object "
            "(total_violations, compliance_score)."
        ),
        agent=compliance_agent,
        context=[t1_usage],
    )

    t3_drift = Task(
        description=(
            f"Compare spec YAML props (from {od / 'specs'}) against TSX props "
            f"(from {od / 'src'}) and Markdown documentation (from {od / 'docs' / 'components'}). "
            "Classify each inconsistency as auto-fixable or re-run-required. "
            "Patch auto-fixable docs Markdown files in-place. "
            "Write the drift report to reports/drift-report.json."
        ),
        expected_output=(
            "JSON file at reports/drift-report.json with an inconsistencies array "
            "(each entry: component, prop, fixable, action, description). "
            "Auto-fixable Markdown docs updated in-place."
        ),
        agent=drift_agent,
        context=[t2_compliance],
    )

    t4_completeness = Task(
        description=(
            f"For each component listed in {od / 'docs' / 'component-index.json'} "
            "(if present) or inferred from spec files, check stage completeness: "
            "spec_validated, code_generated, a11y_passed, tests_written, docs_generated. "
            "Identify components stuck at a stage and recommend interventions. "
            "Write the report to reports/pipeline-completeness.json."
        ),
        expected_output=(
            "JSON file at reports/pipeline-completeness.json with a components array "
            "(each entry: name, stages, completeness_score, stuck_at, intervention)."
        ),
        agent=completeness_agent,
        context=[t3_drift],
    )

    t5_breakage = Task(
        description=(
            f"Read test failure data from reports/generation-summary.json and "
            f"reports/test-results.json (if present) under {od}. "
            f"Load the dependency graph from {od / 'dependency_graph.json'} (if present). "
            "For each failing component, walk the dependency chain and classify the "
            "failure as root-cause or downstream. "
            "Write the report to reports/breakage-correlation.json."
        ),
        expected_output=(
            "JSON file at reports/breakage-correlation.json with a failures array "
            "(each entry: component, failure_type, classification, dependency_chain, "
            "root_cause_component)."
        ),
        agent=breakage_agent,
        context=[t4_completeness],
    )

    return Crew(
        agents=[usage_agent, compliance_agent, drift_agent, completeness_agent, breakage_agent],
        tasks=[t1_usage, t2_compliance, t3_drift, t4_completeness, t5_breakage],
        verbose=False,
    )

