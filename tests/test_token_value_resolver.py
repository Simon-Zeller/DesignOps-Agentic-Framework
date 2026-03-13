"""Tests for token_value_resolver.resolve_token and classify_tier."""
from daf.tools.token_value_resolver import resolve_token, classify_tier

COMPILED = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}


def test_resolves_known_token():
    result = resolve_token("color.interactive.default", COMPILED)
    assert result == "#005FCC"


def test_returns_none_for_unknown_token():
    result = resolve_token("color.unknown.token", COMPILED)
    assert result is None


def test_classifies_semantic_token():
    tier = classify_tier("color.interactive.default")
    assert tier == "semantic"


def test_classifies_global_token():
    tier = classify_tier("color.global.blue-60")
    assert tier == "global"


def test_classifies_component_token():
    tier = classify_tier("button.background.default")
    assert tier == "component"
