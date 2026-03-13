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


def test_render_validation_with_renderer_available(tmp_path):
    """When Playwright is available and render_component is mocked, results are recorded."""
    from daf.agents.render_validation import _validate_renders

    _write_generated_components(tmp_path)

    # Write intent manifests so variants are resolved
    manifests = [{"component_name": "Button", "tier": "simple", "variants": ["primary"]}]
    (tmp_path / "intent_manifests.json").write_text(json.dumps(manifests))

    fake_render = {"path": str(tmp_path / "screenshots/Button/primary.png"), "width": 80, "height": 40, "render_errors": []}

    with patch("daf.agents.render_validation.check_renderer_available", return_value=True), \
         patch("daf.agents.render_validation.render_component", return_value=fake_render):
        _validate_renders(str(tmp_path))

    output_path = tmp_path / "render_validation_output.json"
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data["render_available"] is True
    assert len(data["results"]) == 1
    assert data["results"][0]["render_pass"] is True


def test_render_validation_skips_dirs_with_no_source_tsx(tmp_path):
    """Component dirs that only contain test/story files are skipped."""
    from daf.agents.render_validation import _validate_renders

    # Create a component dir with only test and story files (no source tsx)
    comp_dir = tmp_path / "src" / "components" / "EmptyComp"
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "EmptyComp.test.tsx").write_text("// test")
    (comp_dir / "EmptyComp.stories.tsx").write_text("// stories")

    with patch("daf.tools.playwright_renderer.check_renderer_available", return_value=False):
        _validate_renders(str(tmp_path))

    output_path = tmp_path / "render_validation_output.json"
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    # No results since source tsx was skipped
    assert data["results"] == []
