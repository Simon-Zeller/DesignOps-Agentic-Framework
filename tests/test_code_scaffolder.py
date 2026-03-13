"""Unit tests for code_scaffolder — TSX skeleton, story exports, accessibility placeholder."""
from __future__ import annotations


SAMPLE_MANIFEST = {
    "component_name": "Button",
    "variants": ["primary", "secondary", "ghost"],
    "states": ["default", "hover", "disabled"],
    "token_bindings": [
        {"key": "background", "token": "color.interactive.default"},
        {"key": "foreground", "token": "color.interactive.foreground"},
    ],
    "layout": {"model": "flex", "direction": "row", "align": "center"},
    "aria": {"role": "button", "attrs": ["aria-label", "aria-disabled"], "keyboard": ["Enter", "Space"]},
}


def test_tsx_skeleton_contains_component_name_and_token_placeholders():
    """scaffold_tsx returns a string with export function and token placeholders."""
    from daf.tools.code_scaffolder import scaffold_tsx

    result = scaffold_tsx(SAMPLE_MANIFEST)

    assert "export function Button" in result
    assert "data-testid" in result
    # Each token binding key should appear somewhere in the rendered TSX
    assert "background" in result
    assert "foreground" in result


def test_story_file_contains_named_exports_per_variant():
    """scaffold_stories returns a string with named exports for each variant."""
    from daf.tools.code_scaffolder import scaffold_stories

    result = scaffold_stories(SAMPLE_MANIFEST)

    assert "export const Primary" in result
    assert "export const Secondary" in result
    assert "export const Ghost" in result


def test_test_skeleton_has_accessibility_placeholder():
    """scaffold_tests returns a string whose last non-empty line is the a11y placeholder."""
    from daf.tools.code_scaffolder import scaffold_tests

    result = scaffold_tests(SAMPLE_MANIFEST)

    non_empty_lines = [l for l in result.splitlines() if l.strip()]
    assert non_empty_lines[-1].strip() == "// @accessibility-placeholder"
