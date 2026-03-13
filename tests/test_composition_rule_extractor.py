"""Unit tests for CompositionRuleExtractor tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_composition_rule_extractor_reads_audit_when_present(tmp_path):
    """CompositionRuleExtractor reads rules from composition-audit.json when present."""
    from daf.tools.composition_rule_extractor import CompositionRuleExtractor

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    audit = {
        "rules": [
            {
                "component": "Button",
                "allowed_children": [],
                "forbidden_children": ["Button"],
            }
        ]
    }
    (reports_dir / "composition-audit.json").write_text(json.dumps(audit))

    extractor = CompositionRuleExtractor()
    result = extractor._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0]["component"] == "Button"


def test_composition_rule_extractor_falls_back_to_spec_yaml(tmp_path):
    """CompositionRuleExtractor falls back to spec YAML when audit report is absent."""
    from daf.tools.composition_rule_extractor import CompositionRuleExtractor

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "card.spec.yaml").write_text(
        "name: Card\ncomposition:\n  allowed_children:\n    - Text\n    - Button\n"
    )

    extractor = CompositionRuleExtractor()
    result = extractor._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) >= 1


def test_composition_rule_extractor_returns_empty_when_no_sources(tmp_path):
    """CompositionRuleExtractor returns empty list when no audit or specs found."""
    from daf.tools.composition_rule_extractor import CompositionRuleExtractor

    extractor = CompositionRuleExtractor()
    result = extractor._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert result == []
