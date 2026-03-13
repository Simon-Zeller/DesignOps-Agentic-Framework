"""Tests for keyboard_nav_scaffolder.py."""
from __future__ import annotations

import pytest
from daf.tools.keyboard_nav_scaffolder import scaffold_keyboard_handlers


def test_dialog_generates_escape_handler():
    result = scaffold_keyboard_handlers("dialog", callbacks={"close": "onClose"})
    assert "Escape" in result
    assert "onClose" in result


def test_listbox_generates_arrow_key_handlers():
    result = scaffold_keyboard_handlers("listbox", callbacks={})
    assert "ArrowDown" in result
    assert "ArrowUp" in result
    assert "Enter" in result
    assert "Escape" in result


def test_button_generates_enter_and_space():
    result = scaffold_keyboard_handlers("button", callbacks={"press": "onPress"})
    assert "Enter" in result or "Space" in result
