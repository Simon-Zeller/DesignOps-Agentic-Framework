"""Tests for prose_generator.build_narrative_prompt."""
from daf.tools.prose_generator import build_narrative_prompt

BRAND = {"archetype": "minimalist", "a11y_level": "AA", "modular_scale": 1.25}
DECISIONS = [{"title": "Archetype Selection", "decision": "Use minimalist archetype."}]


def test_prompt_contains_archetype():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert "minimalist" in prompt


def test_prompt_contains_a11y_level():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert "AA" in prompt


def test_prompt_is_non_empty_string():
    prompt = build_narrative_prompt(BRAND, DECISIONS)
    assert isinstance(prompt, str) and len(prompt) > 20


def test_prompt_with_empty_decisions():
    prompt = build_narrative_prompt(BRAND, [])
    assert isinstance(prompt, str)  # never raises
