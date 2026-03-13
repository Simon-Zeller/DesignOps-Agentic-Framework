"""Unit tests for render_validation agent — sets render_available False in Playwright-less env."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _write_generated_components(output_dir: Path) -> None:
    """Write a minimal component file structure for validation."""
    comp_dir = output_dir / "src" / "components" / "Button"
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "Button.tsx").write_text("export function Button() { return <button />; }\n")


def test_render_validation_sets_render_available_false(tmp_path):
    """When Playwright is unavailable, render_validation_output.json has render_available=False."""
    from daf.agents.render_validation import _validate_renders

    _write_generated_components(tmp_path)

    with patch("daf.tools.playwright_renderer.check_renderer_available", return_value=False):
        _validate_renders(str(tmp_path))

    output_path = tmp_path / "render_validation_output.json"
    assert output_path.exists(), "render_validation_output.json was not created"

    data = json.loads(output_path.read_text())
    assert data["render_available"] is False
