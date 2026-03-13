"""Tests for scale_visualizer.visualize_token."""
from daf.tools.scale_visualizer import visualize_token


def test_color_token_shows_swatch():
    result = visualize_token("color.interactive.default", "#005FCC")
    assert "■" in result or "#005FCC" in result


def test_spacing_token_shows_dash():
    result = visualize_token("space.4", "16px")
    assert "16px" in result


def test_non_color_non_spacing_returns_value():
    result = visualize_token("font.size.md", "16px")
    assert "16px" in result
