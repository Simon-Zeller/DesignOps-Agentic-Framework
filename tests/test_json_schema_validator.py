"""Tests for json_schema_validator.py."""
from __future__ import annotations

import pytest
from daf.tools.json_schema_validator import validate_spec_schema

MINIMAL_SCHEMA = {
    "type": "object",
    "required": ["component", "variants", "states", "tokens", "a11y"],
    "properties": {
        "component": {"type": "string"},
        "variants": {"type": "array"},
        "states": {},
        "tokens": {"type": "object"},
        "a11y": {"type": "object"},
    },
}


def test_valid_spec_passes():
    spec = {
        "component": "Button",
        "variants": ["primary", "secondary"],
        "states": {"default": {}, "hover": {}},
        "tokens": {"background": "color.interactive.default"},
        "a11y": {"role": "button"},
    }
    result = validate_spec_schema(spec, MINIMAL_SCHEMA)
    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_required_field_returns_error():
    spec = {
        "component": "Button",
        # missing "variants", "states", "tokens", "a11y"
    }
    result = validate_spec_schema(spec, MINIMAL_SCHEMA)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    # At least one error should reference "variants"
    fields = [e.get("field", "") for e in result["errors"]]
    assert any("variants" in f for f in fields)
