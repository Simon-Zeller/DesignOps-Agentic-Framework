"""Unit tests for intent_extraction agent — produces manifests for all queued components."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


def _write_scope_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "components": [
            {"name": "Box", "tier": "primitive"},
            {"name": "Button", "tier": "simple"},
        ]
    }
    (output_dir / "scope_classifier_output.json").write_text(json.dumps(data))


def _write_fixture_specs(output_dir: Path) -> None:
    specs_dir = output_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    (specs_dir / "box.spec.yaml").write_text("component: Box\n")
    (specs_dir / "button.spec.yaml").write_text(
        "component: Button\nvariants:\n  - primary\n  - secondary\n"
    )


def _write_compiled_tokens(output_dir: Path) -> None:
    tokens_dir = output_dir / "tokens" / "compiled"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    (tokens_dir / "flat.json").write_text(json.dumps({
        "color.interactive.default": "#005FCC",
        "color.interactive.foreground": "#FFFFFF",
    }))


def test_intent_extraction_produces_manifests(tmp_path):
    """Agent writes intent_manifests.json with one manifest per component."""
    from daf.agents.intent_extraction import _extract_intents

    _write_scope_output(tmp_path)
    _write_fixture_specs(tmp_path)
    _write_compiled_tokens(tmp_path)

    _extract_intents(str(tmp_path))

    manifest_path = tmp_path / "intent_manifests.json"
    assert manifest_path.exists(), "intent_manifests.json was not created"

    data = json.loads(manifest_path.read_text())
    assert len(data) == 2
    for manifest in data:
        assert "component_name" in manifest
        assert "layout" in manifest
        assert "token_bindings" in manifest
        assert "aria" in manifest
