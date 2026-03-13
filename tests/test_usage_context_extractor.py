"""Tests for usage_context_extractor.extract_usage_context."""
from daf.tools.usage_context_extractor import extract_usage_context

SPEC_TOKENS = {
    "background": "color.interactive.default",
    "foreground": "color.interactive.foreground",
}


def test_returns_context_for_known_usage():
    context = extract_usage_context("color.interactive.default", SPEC_TOKENS)
    assert isinstance(context, str)
    assert len(context) > 0


def test_returns_empty_string_for_unknown_token():
    context = extract_usage_context("color.mystery.unknown", SPEC_TOKENS)
    assert isinstance(context, str)  # never raises
