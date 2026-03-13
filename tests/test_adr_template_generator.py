"""Tests for adr_template_generator.generate_adr and slugify_title."""
from daf.tools.adr_template_generator import generate_adr, slugify_title

DECISION = {
    "title": "Archetype Selection",
    "context": "The brand required a visual style.",
    "decision": "We selected the minimalist archetype.",
    "consequences": "Fewer color tokens, simpler type scale.",
}


def test_adr_contains_context_section():
    adr = generate_adr(DECISION)
    assert "## Context" in adr or "Context" in adr


def test_adr_contains_decision_section():
    adr = generate_adr(DECISION)
    assert "## Decision" in adr or "Decision" in adr


def test_adr_contains_consequences_section():
    adr = generate_adr(DECISION)
    assert "## Consequences" in adr or "Consequences" in adr


def test_slugify_basic_title():
    assert slugify_title("Archetype Selection") == "archetype-selection"


def test_slugify_strips_special_chars():
    assert slugify_title("Token Scale Algorithm (v2)") == "token-scale-algorithm-v2"
