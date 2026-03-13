"""Unit tests for playwright_renderer — render_available False and screenshot path."""
from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock


def test_render_available_false_when_browser_not_found():
    """check_renderer_available() returns False when no browser binary is found."""
    from daf.tools.playwright_renderer import check_renderer_available

    with patch("daf.tools.playwright_renderer.shutil.which", return_value=None):
        result = check_renderer_available()

    assert result is False


def test_returns_screenshot_path_on_successful_render(tmp_path):
    """render_component returns a dict with path, width, height, and render_errors."""
    from daf.tools.playwright_renderer import render_component

    screenshots_dir = tmp_path / "screenshots"

    fake_result = {
        "path": str(screenshots_dir / "Button" / "primary.png"),
        "width": 100,
        "height": 50,
        "render_errors": [],
    }

    with patch("daf.tools.playwright_renderer._do_render", return_value=fake_result):
        result = render_component("Button", "primary", str(tmp_path))

    assert result["width"] == 100
    assert result["height"] == 50
    assert result["render_errors"] == []
    assert "Button" in result["path"]
    assert "primary" in result["path"]


def test_do_render_returns_fallback_when_playwright_not_installed(tmp_path):
    """_do_render returns a zero-dimension dict when playwright is not installed."""
    from daf.tools.playwright_renderer import _do_render

    # Remove playwright from sys.modules so the import inside _do_render fails
    removed = sys.modules.pop("playwright", None)
    removed_sync = sys.modules.pop("playwright.sync_api", None)
    try:
        with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
            result = _do_render("Box", "default", str(tmp_path))
    finally:
        if removed is not None:
            sys.modules["playwright"] = removed
        if removed_sync is not None:
            sys.modules["playwright.sync_api"] = removed_sync

    assert result["width"] == 0
    assert result["height"] == 0
    assert result["path"] == ""
    assert result["render_errors"] == ["playwright not installed"]
