"""Tests for search_index_builder.build_index_entries."""
from daf.tools.search_index_builder import build_index_entries

BUTTON_MD = """# Button

A pressable component.

## Props

The Button accepts label, disabled, and onPress.

## Usage

Import and use it.
"""


def test_returns_list_of_entries():
    entries = build_index_entries(BUTTON_MD, "docs/components/Button.md")
    assert isinstance(entries, list)
    assert len(entries) > 0


def test_each_entry_has_required_keys():
    entries = build_index_entries(BUTTON_MD, "docs/components/Button.md")
    for entry in entries:
        assert "id" in entry
        assert "title" in entry
        assert "content" in entry
        assert "path" in entry


def test_content_strips_markdown_formatting():
    entries = build_index_entries(
        "# Button\n\nA **pressable** component.", "docs/components/Button.md"
    )
    for entry in entries:
        assert "**" not in entry["content"]
        assert "#" not in entry["content"]


def test_empty_markdown_returns_empty_list():
    entries = build_index_entries("", "docs/components/Empty.md")
    assert entries == []
