"""Tests for primitive_registry.py."""
from __future__ import annotations

import pytest
from daf.tools.primitive_registry import is_primitive, get_all_primitives

BASE_PRIMITIVES = {"Box", "Stack", "Grid", "Text", "Icon", "Pressable", "Divider", "Spacer", "ThemeProvider"}
EXPORT_ALIASES = {"HStack", "VStack"}


def test_known_primitive_recognized():
    assert is_primitive("Box") is True
    assert is_primitive("Pressable") is True
    assert is_primitive("Text") is True


def test_unknown_element_not_primitive():
    assert is_primitive("Dialog") is False
    assert is_primitive("Button") is False
    assert is_primitive("@radix-ui/react-dialog") is False


def test_all_primitives_and_exports_registered():
    primitives = get_all_primitives()
    expected = BASE_PRIMITIVES | EXPORT_ALIASES
    for name in expected:
        assert name in primitives, f"Expected {name!r} in registry"
