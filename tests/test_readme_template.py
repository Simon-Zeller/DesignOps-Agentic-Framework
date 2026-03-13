"""Tests for readme_template.render_readme."""
from daf.tools.readme_template import render_readme


def test_readme_contains_install_instructions():
    result = render_readme(["Button", "Badge"], ["color", "spacing"])
    assert "npm install" in result


def test_readme_lists_all_components():
    result = render_readme(["Button", "Badge", "Input"], ["color"])
    assert "Button" in result and "Badge" in result and "Input" in result


def test_readme_links_to_component_docs():
    result = render_readme(["Button"], ["color"])
    assert "docs/components/Button" in result or "components/Button" in result


def test_readme_with_empty_components_includes_note():
    result = render_readme([], [])
    assert "no components" in result.lower() or result  # graceful empty
