"""Unit tests for ContextFormatter tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_context_formatter_returns_cursorrules_string(tmp_path):
    """ContextFormatter returns a non-empty cursorrules string."""
    from daf.tools.context_formatter import ContextFormatter

    registry = {
        "components": [{"name": "Button", "props": [{"name": "variant", "type": "string"}]}],
        "tokens": [],
        "composition_rules": [],
        "compliance_rules": {},
    }

    formatter = ContextFormatter()
    result = formatter._run(registry=registry, output_dir=str(tmp_path))

    assert isinstance(result, dict)
    assert "cursorrules" in result
    assert isinstance(result["cursorrules"], str)
    assert len(result["cursorrules"]) > 0


def test_context_formatter_returns_copilot_instructions_string(tmp_path):
    """ContextFormatter returns a non-empty copilot_instructions string."""
    from daf.tools.context_formatter import ContextFormatter

    registry = {
        "components": [],
        "tokens": [],
        "composition_rules": [],
        "compliance_rules": {},
    }

    formatter = ContextFormatter()
    result = formatter._run(registry=registry, output_dir=str(tmp_path))

    assert "copilot_instructions" in result
    assert isinstance(result["copilot_instructions"], str)


def test_context_formatter_includes_component_names(tmp_path):
    """ContextFormatter output references component names from the registry."""
    from daf.tools.context_formatter import ContextFormatter

    registry = {
        "components": [{"name": "Button", "props": []}],
        "tokens": [],
        "composition_rules": [],
        "compliance_rules": {},
    }

    formatter = ContextFormatter()
    result = formatter._run(registry=registry, output_dir=str(tmp_path))

    assert "Button" in result["cursorrules"] or "Button" in result["copilot_instructions"]
