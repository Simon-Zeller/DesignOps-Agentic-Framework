"""Tests for metadata_tagger.tag_entry."""
from daf.tools.metadata_tagger import tag_entry


def test_component_file_gets_component_category():
    entry = {"id": "1", "title": "Button", "content": "...", "path": "docs/components/Button.md"}
    tagged = tag_entry(entry, "docs/components/Button.md")
    assert tagged["category"] == "component"


def test_token_catalog_gets_token_category():
    entry = {"id": "2", "title": "color.interactive", "content": "...", "path": "docs/tokens/catalog.md"}
    tagged = tag_entry(entry, "docs/tokens/catalog.md")
    assert tagged["category"] == "token"


def test_decision_file_gets_decision_category():
    entry = {"id": "3", "title": "ADR-001", "content": "...", "path": "docs/decisions/adr-archetype.md"}
    tagged = tag_entry(entry, "docs/decisions/adr-archetype.md")
    assert tagged["category"] == "decision"


def test_readme_gets_readme_category():
    entry = {"id": "4", "title": "README", "content": "...", "path": "docs/README.md"}
    tagged = tag_entry(entry, "docs/README.md")
    assert tagged["category"] == "readme"
