"""Integration test for Design-to-Code Crew — full run writes expected file tree."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _prepare_output_dir(output_dir: Path) -> None:
    """Set up the minimal input artifacts the crew expects."""
    # Spec files
    specs_dir = output_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    (specs_dir / "box.spec.yaml").write_text("component: Box\n")
    (specs_dir / "button.spec.yaml").write_text(
        "component: Button\nvariants:\n  - primary\n  - secondary\n"
    )

    # Compiled tokens
    tokens_dir = output_dir / "tokens" / "compiled"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    (tokens_dir / "flat.json").write_text(json.dumps({
        "color.interactive.default": "#005FCC",
        "color.interactive.foreground": "#FFFFFF",
        "space.4": "16px",
    }))


def test_full_crew_run_writes_expected_file_tree(tmp_path):
    """Design-to-Code Crew end-to-end: given specs + tokens, writes TSX, tests, stories, and report."""
    _prepare_output_dir(tmp_path)

    with patch("daf.tools.playwright_renderer.check_renderer_available", return_value=False):
        from daf.crews.design_to_code import create_design_to_code_crew
        crew = create_design_to_code_crew(str(tmp_path))
        crew.kickoff()

    # Component files should be written
    src_dir = tmp_path / "src"
    assert src_dir.exists(), "src/ directory was not created"

    # Report must exist and be valid JSON
    report_path = tmp_path / "reports" / "generation-summary.json"
    assert report_path.exists(), "generation-summary.json was not created"
    data = json.loads(report_path.read_text())
    assert "total_components" in data
    assert "stub" not in data  # must not be stub output
