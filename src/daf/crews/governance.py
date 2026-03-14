"""Governance Crew (Agents 26–30, Phase 4b).

Replaces the stub with a real CrewAI Crew housing five agents — Ownership,
Workflow, Deprecation, RFC, and Quality Gate — running tasks T1–T5 in order.

Pre-flight guard: raises ``RuntimeError`` if ``docs/component-index.json`` is
absent or empty, as the Quality Gate Agent depends on Documentation Crew output.
"""
from __future__ import annotations

from pathlib import Path

from crewai import Crew, Task

from daf.agents.ownership import create_ownership_agent
from daf.agents.workflow import create_workflow_agent
from daf.agents.deprecation import create_deprecation_agent
from daf.agents.rfc import create_rfc_agent
from daf.agents.quality_gate import create_quality_gate_agent
from daf.agents.exit_criteria import create_exit_criteria_agent

_SONNET_MODEL = "anthropic/claude-sonnet-4-20250514"
_HAIKU_MODEL = "anthropic/claude-sonnet-4-20250514"


def create_governance_crew(output_dir: str) -> Crew:
    """Create the Governance Crew for *output_dir*.

    Pre-flight: verifies ``docs/component-index.json`` exists and is non-empty.

    Args:
        output_dir: Root pipeline output directory.

    Raises:
        RuntimeError: If ``docs/component-index.json`` is absent or empty.

    Returns:
        A :class:`crewai.Crew` with 5 tasks wired T1→T5.
    """
    od = Path(output_dir)
    index_path = od / "docs" / "component-index.json"

    if not index_path.exists():
        raise RuntimeError(
            "Documentation Crew output not found — ensure Phase 4a completes before Phase 4b"
        )

    index_content = index_path.read_text(encoding="utf-8").strip()
    if not index_content or index_content == "{}":
        raise RuntimeError(
            "Documentation Crew output not found — ensure Phase 4a completes before Phase 4b"
        )

    # Instantiate agents
    ownership_agent = create_ownership_agent(_SONNET_MODEL, output_dir)
    workflow_agent = create_workflow_agent(_HAIKU_MODEL, output_dir)
    deprecation_agent = create_deprecation_agent(_HAIKU_MODEL, output_dir)
    rfc_agent = create_rfc_agent(_HAIKU_MODEL, output_dir)
    quality_gate_agent = create_quality_gate_agent(_HAIKU_MODEL, output_dir)
    exit_criteria_agent = create_exit_criteria_agent(_HAIKU_MODEL, output_dir)

    # Define tasks T1–T5
    t1_ownership = Task(
        description=(
            f"Classify each component and token category from {od / 'docs' / 'component-index.json'} "
            f"into a domain using the domains section of {od / 'pipeline-config.json'}. "
            "Detect orphaned components. Write the result to governance/ownership.json."
        ),
        expected_output=(
            "JSON file at governance/ownership.json with component→domain mapping "
            "and a list of orphaned components."
        ),
        agent=ownership_agent,
    )

    t2_workflow = Task(
        description=(
            f"Read quality gate thresholds from {od / 'pipeline-config.json'} and the "
            "domain structure from governance/ownership.json. Generate the workflow state "
            "machine definition and write it to governance/workflow.json."
        ),
        expected_output=(
            "JSON file at governance/workflow.json with token_change_pipeline and "
            "component_change_pipeline state machine definitions."
        ),
        agent=workflow_agent,
    )

    t3_deprecation = Task(
        description=(
            f"Read the lifecycle config from {od / 'pipeline-config.json'} and component "
            "data from governance/ownership.json. Classify each component's stability status "
            "and generate the deprecation policy. Write to governance/deprecation-policy.json."
        ),
        expected_output=(
            "JSON file at governance/deprecation-policy.json with grace periods, "
            "migration guide requirements, and component lifecycle statuses."
        ),
        agent=deprecation_agent,
    )

    t4_rfc = Task(
        description=(
            "Read governance/workflow.json to determine when RFCs are required. "
            "Generate the RFC template and process definition. "
            "Write docs/templates/rfc-template.md and governance/process.json."
        ),
        expected_output=(
            "Markdown RFC template at docs/templates/rfc-template.md and "
            "process definition JSON at governance/process.json."
        ),
        agent=rfc_agent,
    )

    t5_quality_gate = Task(
        description=(
            "Read reports/quality-scorecard.json and the docs/ directory. "
            "Evaluate five quality gates (coverage ≥ 80%, zero a11y critical violations, "
            "no phantom token refs, all components have docs, all have usage examples) "
            "per component. Write reports/governance/quality-gates.json. "
            "Generate tests/tokens.test.ts, tests/a11y.test.ts, "
            "tests/composition.test.ts, tests/compliance.test.ts."
        ),
        expected_output=(
            "JSON file at reports/governance/quality-gates.json with per-component gate pass/fail, "
            "and four TypeScript test suites in tests/."
        ),
        agent=quality_gate_agent,
    )

    t6_exit_criteria = Task(
        description=(
            f"Run all 15 §8 exit criteria checks against {output_dir}. "
            "Evaluate token JSON validity, DTCG conformance, reference resolution, "
            "contrast ratios, CSS refs, TypeScript compilation, npm build, "
            "test results, and governance report scores. "
            "Write the structured report to reports/exit-criteria.json."
        ),
        expected_output=(
            "JSON file at reports/exit-criteria.json with isComplete flag and "
            "all 15 criterion results (id, description, severity, passed, detail)."
        ),
        agent=exit_criteria_agent,
    )

    return Crew(
        agents=[
            ownership_agent,
            workflow_agent,
            deprecation_agent,
            rfc_agent,
            quality_gate_agent,
            exit_criteria_agent,
        ],
        tasks=[t1_ownership, t2_workflow, t3_deprecation, t4_rfc, t5_quality_gate, t6_exit_criteria],
        verbose=False,
    )

