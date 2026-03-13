"""Tests for token_ref_checker.py."""
from __future__ import annotations

import pytest
from daf.tools.token_ref_checker import check_token_refs


COMPILED = {
    "color.brand.primary": "#005FCC",
    "color.interactive.default": "#005FCC",
    "color.interactive.foreground": "#FFFFFF",
    "radius.md": "8px",
}


def test_all_refs_resolve():
    spec_tokens = {"background": "color.brand.primary", "radius": "radius.md"}
    result = check_token_refs(spec_tokens, COMPILED)
    assert result["all_resolved"] is True
    assert result["unresolved"] == []


def test_unresolved_ref_detected():
    spec_tokens = {"color": "color.status.info"}
    result = check_token_refs(spec_tokens, COMPILED)
    assert result["all_resolved"] is False
    assert "color.status.info" in result["unresolved"]


def test_empty_spec_tokens():
    result = check_token_refs({}, COMPILED)
    assert result["all_resolved"] is True
    assert result["unresolved"] == []
