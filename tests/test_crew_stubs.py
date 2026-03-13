"""Tests for crew stub modules (p09-pipeline-orchestrator, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Parametrize: for each crew, define (factory_import, required_outputs)
# ---------------------------------------------------------------------------

CREW_OUTPUT_SPECS = [
    (
        "daf.crews.token_engine",
        "create_token_engine_crew",
        [
            "tokens/compiled/variables.css",
            "tokens/compiled/variables-light.css",
            "tokens/compiled/variables-dark.css",
            "tokens/compiled/variables-high-contrast.css",
            "tokens/compiled/variables.scss",
            "tokens/compiled/tokens.ts",
            "tokens/compiled/tokens.json",
            "tokens/diff.json",
        ],
    ),
    (
        "daf.crews.design_to_code",
        "create_design_to_code_crew",
        [
            "src/primitives/index.ts",
            "src/components/index.ts",
            "src/index.ts",
            "reports/generation-summary.json",
        ],
    ),
    (
        "daf.crews.component_factory",
        "create_component_factory_crew",
        [
            "reports/quality-scorecard.json",
            "reports/a11y-audit.json",
            "reports/composition-audit.json",
        ],
    ),
    (
        "daf.crews.documentation",
        "create_documentation_crew",
        [
            "docs/README.md",
            "docs/tokens.md",
            "docs/search-index.json",
            "docs/decisions/generation-narrative.md",
            "docs/changelog.md",
        ],
    ),
    (
        "daf.crews.governance",
        "create_governance_crew",
        [
            "governance/ownership.json",
            "governance/quality-gates.json",
            "governance/deprecation-policy.json",
            "governance/workflow.json",
            "docs/templates/rfc-template.md",
            "tests/tokens.test.ts",
            "tests/a11y.test.ts",
            "tests/composition.test.ts",
            "tests/compliance.test.ts",
        ],
    ),
    (
        "daf.crews.ai_semantic_layer",
        "create_ai_semantic_layer_crew",
        [
            "registry/components.json",
            "registry/tokens.json",
            "registry/composition-rules.json",
            "registry/compliance-rules.json",
            ".cursorrules",
            "copilot-instructions.md",
            "ai-context.json",
        ],
    ),
    (
        "daf.crews.analytics",
        "create_analytics_crew",
        [
            "reports/token-compliance.json",
            "reports/drift-report.json",
        ],
    ),
    (
        "daf.crews.release",
        "create_release_crew",
        [
            "package.json",
        ],
    ),
]


# ---------------------------------------------------------------------------
# test_token_engine_stub_writes_required_outputs
# ---------------------------------------------------------------------------

def test_token_engine_stub_writes_required_outputs(tmp_path: Path) -> None:
    """Token Engine stub writes all required output files."""
    # Provide raw token input files
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    for name in ("base.tokens.json", "semantic.tokens.json", "component.tokens.json"):
        (tokens_dir / name).write_text('{"stub": true}')

    from daf.crews.token_engine import create_token_engine_crew

    crew = create_token_engine_crew(output_dir=str(tmp_path))
    crew.kickoff()

    assert (tmp_path / "tokens" / "compiled" / "variables.css").exists()
    assert (tmp_path / "tokens" / "compiled" / "variables-light.css").exists()
    assert (tmp_path / "tokens" / "diff.json").exists()


# ---------------------------------------------------------------------------
# test_all_crew_stubs_write_minimum_outputs (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "module_path,factory_name,expected_files",
    CREW_OUTPUT_SPECS,
    ids=[spec[1].replace("create_", "").replace("_crew", "") for spec in CREW_OUTPUT_SPECS],
)
def test_all_crew_stubs_write_minimum_outputs(
    tmp_path: Path,
    module_path: str,
    factory_name: str,
    expected_files: list[str],
) -> None:
    """Each stub crew writes all files from its §3.6 Writes column."""
    import importlib

    mod = importlib.import_module(module_path)
    factory = getattr(mod, factory_name)
    crew = factory(output_dir=str(tmp_path))
    crew.kickoff()

    for rel_path in expected_files:
        full_path = tmp_path / rel_path
        assert full_path.exists(), f"{factory_name}: expected output {rel_path!r} not written to {tmp_path}"
