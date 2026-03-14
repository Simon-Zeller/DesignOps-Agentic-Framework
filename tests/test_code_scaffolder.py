"""Unit tests for code_scaffolder — TSX, story, and test file generation."""
from __future__ import annotations


SAMPLE_MANIFEST = {
    "component_name": "Button",
    "description": "Interactive button component for primary actions.",
    "variants": ["primary", "secondary", "ghost"],
    "states": {"default": {}, "hover": {}, "disabled": {}},
    "props": [
        {"name": "children", "type": "React.ReactNode", "required": True, "description": "Button content"},
        {"name": "variant", "type": "string", "required": False, "default": "primary", "description": "Visual style"},
        {"name": "disabled", "type": "boolean", "required": False, "default": False, "description": "Disables the button"},
        {"name": "onClick", "type": "() => void", "required": False, "description": "Click handler"},
    ],
    "token_bindings": [
        {"key": "backgroundColor", "token": "color.interactive.default"},
        {"key": "color", "token": "color.interactive.foreground"},
    ],
    "layout": {"model": "flex", "direction": "row", "align": "center"},
    "aria": {"role": "button", "attrs": ["aria-label", "aria-disabled"], "keyboard": ["Enter", "Space"]},
}


def test_tsx_contains_component_name_and_semantic_element():
    """scaffold_tsx generates a <button> element with typed props interface."""
    from daf.tools.code_scaffolder import scaffold_tsx

    result = scaffold_tsx(SAMPLE_MANIFEST)

    assert "export function Button" in result
    assert "export interface ButtonProps" in result
    assert "data-testid" in result
    assert "<button" in result  # semantic HTML from role=button
    assert "children?: React.ReactNode" not in result  # children is required
    assert "children: React.ReactNode" in result


def test_tsx_applies_token_bindings_as_css_vars():
    """scaffold_tsx applies token bindings as CSS custom property var() values."""
    from daf.tools.code_scaffolder import scaffold_tsx

    result = scaffold_tsx(SAMPLE_MANIFEST)

    assert "var(--color-interactive-default)" in result
    assert "var(--color-interactive-foreground)" in result


def test_tsx_includes_typed_props():
    """scaffold_tsx generates TypeScript props from manifest."""
    from daf.tools.code_scaffolder import scaffold_tsx

    result = scaffold_tsx(SAMPLE_MANIFEST)

    assert "disabled" in result
    assert "onClick" in result


def test_story_file_contains_named_exports_per_variant():
    """scaffold_stories returns a string with named exports for each variant."""
    from daf.tools.code_scaffolder import scaffold_stories

    result = scaffold_stories(SAMPLE_MANIFEST)

    assert "export const Primary" in result
    assert "export const Secondary" in result
    assert "export const Ghost" in result
    assert "export const Default" in result


def test_story_file_has_argtypes():
    """scaffold_stories generates argTypes from props."""
    from daf.tools.code_scaffolder import scaffold_stories

    result = scaffold_stories(SAMPLE_MANIFEST)

    assert "argTypes" in result
    assert "disabled" in result


def test_test_file_has_variant_and_interaction_tests():
    """scaffold_tests generates tests for variants, disabled state, and click handler."""
    from daf.tools.code_scaffolder import scaffold_tests

    result = scaffold_tests(SAMPLE_MANIFEST)

    assert "renders without crashing" in result
    assert "renders primary variant" in result
    assert "renders disabled state" in result
    assert "calls onClick handler" in result
    assert "applies custom className" in result


def test_test_file_has_keyboard_interaction_tests():
    """scaffold_tests generates keyboard interaction tests from aria spec."""
    from daf.tools.code_scaffolder import scaffold_tests

    result = scaffold_tests(SAMPLE_MANIFEST)

    assert "responds to Enter key" in result
    assert "responds to Space key" in result
