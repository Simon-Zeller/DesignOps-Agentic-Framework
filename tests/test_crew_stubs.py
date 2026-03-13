"""Tests for crew stub modules (p09-pipeline-orchestrator, TDD red phase)."""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Parametrize: for each crew, define (factory_import, required_outputs)
# ---------------------------------------------------------------------------

CREW_OUTPUT_SPECS = [
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
            "docs/tokens/catalog.md",
            "docs/search-index.json",
            "docs/decisions/generation-narrative.md",
        ],
    ),
    # governance crew graduated from StubCrew to real crewai.Crew in p14;
    # its contract is tested in tests/test_governance_crew.py instead.
    # ai_semantic_layer crew graduated from StubCrew to real crewai.Crew in p16;
    # its contract is tested in tests/test_ai_semantic_layer_crew.py instead.
    # release crew graduated from StubCrew to real crewai.Crew in p17;
    # its contract is tested in tests/test_release_crew.py instead.
]


# ---------------------------------------------------------------------------
# test_token_engine_stub_writes_required_outputs
# ---------------------------------------------------------------------------

def test_token_engine_stub_writes_required_outputs(tmp_path: Path) -> None:
    """Token Engine crew writes all required output files when given valid token input."""
    import json as _json
    # Provide minimal valid DTCG token input files
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    semantic = {"color": {"interactive": {"default": {"$type": "color", "$value": "{color.brand.primary}"}}}}
    (tokens_dir / "base.tokens.json").write_text(_json.dumps(base))
    (tokens_dir / "semantic.tokens.json").write_text(_json.dumps(semantic))
    (tokens_dir / "component.tokens.json").write_text(_json.dumps({}))

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
