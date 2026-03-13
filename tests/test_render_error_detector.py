"""Unit tests for render_error_detector — React exception detection and clean log."""
from __future__ import annotations


def test_detects_react_exception_in_console_log():
    """Console log with React error string returns a detected error entry."""
    from daf.tools.render_error_detector import detect_render_errors

    console_log = "Error: Cannot read properties of undefined (reading 'map')"
    errors = detect_render_errors(console_log)

    assert len(errors) == 1
    assert errors[0]["type"] == "react_exception"
    assert "Cannot read properties of undefined" in errors[0]["message"]


def test_returns_empty_list_for_clean_console_log():
    """Console log with only normal output returns []."""
    from daf.tools.render_error_detector import detect_render_errors

    console_log = "React DevTools\ncomponent mounted\nrender complete"
    errors = detect_render_errors(console_log)

    assert errors == []
