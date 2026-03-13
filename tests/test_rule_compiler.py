"""Unit tests for RuleCompiler tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_rule_compiler_writes_valid_json(tmp_path):
    """RuleCompiler writes compliance-rules.json with valid JSON."""
    from daf.tools.rule_compiler import RuleCompiler

    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    (registry_dir / "components.json").write_text(json.dumps([{"name": "Button"}]))
    (registry_dir / "tokens.json").write_text(json.dumps([]))
    (registry_dir / "composition-rules.json").write_text(json.dumps([]))

    compiler = RuleCompiler()
    compiler._run(output_dir=str(tmp_path))

    out_file = tmp_path / "registry" / "compliance-rules.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert isinstance(data, dict)


def test_rule_compiler_output_has_four_required_categories(tmp_path):
    """RuleCompiler output dict contains the four required rule categories."""
    from daf.tools.rule_compiler import RuleCompiler

    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    (registry_dir / "components.json").write_text(json.dumps([]))
    (registry_dir / "tokens.json").write_text(json.dumps([]))
    (registry_dir / "composition-rules.json").write_text(json.dumps([]))

    compiler = RuleCompiler()
    compiler._run(output_dir=str(tmp_path))

    data = json.loads((tmp_path / "registry" / "compliance-rules.json").read_text())
    for key in ("token_rules", "composition_rules", "a11y_rules", "naming_rules"):
        assert key in data, f"Missing category: {key}"


def test_rule_compiler_handles_empty_registries(tmp_path):
    """RuleCompiler does not raise when all registry files are empty arrays."""
    from daf.tools.rule_compiler import RuleCompiler

    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    (registry_dir / "components.json").write_text(json.dumps([]))
    (registry_dir / "tokens.json").write_text(json.dumps([]))
    (registry_dir / "composition-rules.json").write_text(json.dumps([]))

    compiler = RuleCompiler()
    compiler._run(output_dir=str(tmp_path))  # should not raise
