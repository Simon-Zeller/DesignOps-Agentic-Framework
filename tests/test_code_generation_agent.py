"""Unit tests for code_generation agent — writes three files per component and rejection file."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock


def _write_intent_manifests(output_dir: Path, with_bad_token: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifests = [
        {
            "component_name": "Button",
            "variants": ["primary", "secondary"],
            "states": ["default", "hover"],
            "token_bindings": [
                {"key": "background", "token": "color.interactive.default" if not with_bad_token else "color.nonexistent.token"},
            ],
            "layout": {"model": "flex", "direction": "row", "align": "center"},
            "aria": {"role": "button", "attrs": ["aria-label"], "keyboard": ["Enter"]},
        }
    ]
    (output_dir / "intent_manifests.json").write_text(json.dumps(manifests))


def _write_compiled_tokens(output_dir: Path) -> None:
    tokens_dir = output_dir / "tokens" / "compiled"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    (tokens_dir / "flat.json").write_text(json.dumps({
        "color.interactive.default": "#005FCC",
    }))


def test_code_generation_writes_three_files_per_component(tmp_path):
    """Agent writes .tsx, .test.tsx, and .stories.tsx for each component."""
    from daf.agents.code_generation import _generate_code

    _write_intent_manifests(tmp_path)
    _write_compiled_tokens(tmp_path)

    _generate_code(str(tmp_path))

    assert (tmp_path / "src" / "components" / "Button" / "Button.tsx").exists()
    assert (tmp_path / "src" / "components" / "Button" / "Button.test.tsx").exists()
    assert (tmp_path / "src" / "components" / "Button" / "Button.stories.tsx").exists()


def test_code_generation_writes_warning_file_on_unresolvable_token(tmp_path):
    """Agent writes generation-rejection.json with warnings when a token reference can't be resolved."""
    from daf.agents.code_generation import _generate_code

    _write_intent_manifests(tmp_path, with_bad_token=True)
    _write_compiled_tokens(tmp_path)

    _generate_code(str(tmp_path))

    rejection_path = tmp_path / "reports" / "generation-rejection.json"
    assert rejection_path.exists(), "generation-rejection.json was not created"
    data = json.loads(rejection_path.read_text())
    assert len(data["token_warnings"]) >= 1
    assert data["token_warnings"][0]["reason"] == "unresolvable_token_ref"
