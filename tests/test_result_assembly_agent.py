"""Unit tests for result_assembly agent — writes valid generation-summary.json."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _setup_output_dir(output_dir: Path) -> None:
    """Write minimal render_validation_output.json and component files for assembly."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write render outputs
    render_output = {
        "render_available": False,
        "results": [
            {"component": "Button", "render_pass": True, "errors": []}
        ],
    }
    (output_dir / "render_validation_output.json").write_text(json.dumps(render_output))

    # Write generated component files
    comp_dir = output_dir / "src" / "components" / "Button"
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "Button.tsx").write_text("export function Button() { return <button />; }\n")
    (comp_dir / "Button.test.tsx").write_text("// test\n")
    (comp_dir / "Button.stories.tsx").write_text("// stories\n")

    # Write intent manifests
    manifests = [
        {
            "component_name": "Button",
            "variants": ["primary"],
            "token_bindings": [{"key": "bg", "token": "color.default"}],
        }
    ]
    (output_dir / "intent_manifests.json").write_text(json.dumps(manifests))


def test_result_assembly_writes_valid_summary(tmp_path):
    """Agent writes generation-summary.json with valid JSON content."""
    from daf.agents.result_assembly import _assemble_results

    _setup_output_dir(tmp_path)
    _assemble_results(str(tmp_path))

    report_path = tmp_path / "reports" / "generation-summary.json"
    assert report_path.exists(), "generation-summary.json was not created"

    data = json.loads(report_path.read_text())
    assert "total_components" in data
    assert "generated" in data
    assert "failed" in data
    assert "components" in data
