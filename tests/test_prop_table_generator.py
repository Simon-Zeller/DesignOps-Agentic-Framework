"""Tests for prop_table_generator.generate_prop_table."""
from daf.tools.prop_table_generator import generate_prop_table

PROPS = [
    {"name": "label", "type": "string", "required": True, "default": None},
    {"name": "disabled", "type": "boolean", "required": False, "default": False},
]


def test_generates_markdown_table_header():
    table = generate_prop_table(PROPS)
    assert "| Prop |" in table and "| Type |" in table


def test_required_prop_has_no_default_dash():
    table = generate_prop_table(PROPS)
    assert "—" in table  # label has no default


def test_optional_prop_shows_default():
    table = generate_prop_table(PROPS)
    assert "False" in table or "false" in table


def test_empty_props_returns_no_props_note():
    result = generate_prop_table([])
    assert "No props declared" in result
