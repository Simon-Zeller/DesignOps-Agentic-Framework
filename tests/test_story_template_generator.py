"""Unit tests for story_template_generator — one story per variant."""
from __future__ import annotations


def test_generates_one_story_per_variant():
    """generate_stories returns a string with a named export for each variant."""
    from daf.tools.story_template_generator import generate_stories

    result = generate_stories(
        component_name="Button",
        variants=["primary", "secondary", "ghost"],
        states=["default", "hover"],
    )

    assert "export const Primary" in result
    assert "export const Secondary" in result
    assert "export const Ghost" in result
