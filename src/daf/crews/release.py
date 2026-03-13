"""Release Crew (Agents 36–39, Phase 5).

Replaces the StubCrew with a real crewai.Crew housing four agents — Semver,
Release Changelog, Codemod, and Publish — running tasks T1–T6 in sequence.

Pre-flight guard: raises ``RuntimeError`` if
``reports/governance/quality-gates.json`` is absent, as the Semver Agent
depends on Governance Crew output.

Agent 40 (Rollback) is NOT wired into this crew.  It is instantiated by
Agent 6 (First Publish) at pipeline start and invoked at every phase boundary.
"""
from __future__ import annotations

from pathlib import Path

from crewai import Crew, Task

from daf.agents.semver import create_semver_agent
from daf.agents.release_changelog import create_release_changelog_agent
from daf.agents.codemod import create_codemod_agent
from daf.agents.publish import create_publish_agent

_SONNET_MODEL = "claude-3-5-sonnet-20241022"
_HAIKU_MODEL = "claude-3-5-haiku-20241022"


def create_release_crew(output_dir: str) -> Crew:
    """Create the Release Crew for *output_dir*.

    Pre-flight: verifies ``reports/governance/quality-gates.json`` exists.

    Args:
        output_dir: Root pipeline output directory.

    Raises:
        RuntimeError: If ``reports/governance/quality-gates.json`` is absent.

    Returns:
        A :class:`crewai.Crew` with 4 agents and 6 tasks wired T1→T6.
    """
    od = Path(output_dir)
    gate_report = od / "reports" / "governance" / "quality-gates.json"

    if not gate_report.exists():
        raise RuntimeError(
            f"quality-gates.json not found at {gate_report} — "
            "ensure Governance Crew completes before Release Crew"
        )

    # Ensure output directories exist
    (od / "docs" / "codemods").mkdir(parents=True, exist_ok=True)

    # Instantiate agents
    semver_agent = create_semver_agent(_HAIKU_MODEL, output_dir)
    changelog_agent = create_release_changelog_agent(_SONNET_MODEL, output_dir)
    codemod_agent = create_codemod_agent(_HAIKU_MODEL, output_dir)
    publish_agent = create_publish_agent(_HAIKU_MODEL, output_dir)

    # Define tasks T1–T6
    t1_semver = Task(
        description=(
            f"Read {gate_report} and derive the next semantic version string. "
            "Write the version field to reports/generation-summary.json. "
            "If the gate report is unreadable or malformed, fall back to "
            "v0.1.0-experimental and log a warning."
        ),
        expected_output=(
            "Semantic version string (e.g. v1.2.0) written to the version field "
            "of reports/generation-summary.json."
        ),
        agent=semver_agent,
    )

    t2_changelog = Task(
        description=(
            f"Read {gate_report}, component specs from {od / 'specs'}/*.spec.yaml, "
            f"and source components under {od / 'src' / 'components'}. "
            "Generate a human-readable changelog and write it to docs/changelog.md."
        ),
        expected_output=(
            "Markdown changelog at docs/changelog.md listing new components, "
            "breaking changes, deprecations, and quality gate results."
        ),
        agent=changelog_agent,
    )

    t3_codemod = Task(
        description=(
            f"Scan {od / 'src' / 'components'} and {od / 'src' / 'primitives'} "
            "for raw HTML elements (e.g. <button>, <input>) and hardcoded hex "
            "colors that should be replaced with design system tokens. "
            "Generate adoption codemod example files in docs/codemods/ "
            "for each detected pattern, showing before/after snippets."
        ),
        expected_output=(
            "One or more Markdown codemod example files in docs/codemods/ "
            "showing migration from raw HTML / hardcoded colors to design system components."
        ),
        agent=codemod_agent,
    )

    t4_publish_assemble = Task(
        description=(
            f"Read component specs from {od / 'specs'}/*.spec.yaml and the "
            "version from reports/generation-summary.json. "
            "Assemble package.json with correct name, version, and peer dependencies. "
            "Generate src/index.ts barrel file exporting all public components."
        ),
        expected_output=(
            "package.json at the output root with correct version and dependencies, "
            "and src/index.ts barrel exporting all components."
        ),
        agent=publish_agent,
    )

    t5_publish_validate = Task(
        description=(
            "Run npm install, tsc --noEmit, and npm test against the assembled "
            "package. Parse the results and write final_status to "
            "reports/generation-summary.json. "
            "If npm is unavailable, record npm_unavailable warning and continue. "
            "TypeScript compilation failures are Fatal; test failures are Warning."
        ),
        expected_output=(
            "reports/generation-summary.json updated with final_status field "
            "(passed, failed, or npm_unavailable) and a test results summary."
        ),
        agent=publish_agent,
    )

    t6_final_status = Task(
        description=(
            "Read reports/generation-summary.json and verify it contains a "
            "final_status field. If the field is missing, write final_status: failed. "
            "This is a defensive validation step — all prior tasks should have "
            "already written this field."
        ),
        expected_output=(
            "reports/generation-summary.json confirmed to contain final_status. "
            "A brief validation summary is returned."
        ),
        agent=publish_agent,
    )

    return Crew(
        agents=[semver_agent, changelog_agent, codemod_agent, publish_agent],
        tasks=[t1_semver, t2_changelog, t3_codemod, t4_publish_assemble, t5_publish_validate, t6_final_status],
        verbose=False,
    )
