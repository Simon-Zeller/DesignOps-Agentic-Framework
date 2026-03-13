"""Primitive Registry — canonical list of base primitives and exports.

Maintains the 9 base primitives and 11+ exports for the Component Factory Crew.
Used by the Composition Agent to classify JSX elements as primitive or non-primitive.
"""
from __future__ import annotations

_BASE_PRIMITIVES: frozenset[str] = frozenset({
    "Box",
    "Stack",
    "Grid",
    "Text",
    "Icon",
    "Pressable",
    "Divider",
    "Spacer",
    "ThemeProvider",
})

_EXPORT_ALIASES: frozenset[str] = frozenset({
    "HStack",
    "VStack",
})

_ALL_PRIMITIVES: frozenset[str] = _BASE_PRIMITIVES | _EXPORT_ALIASES


def is_primitive(name: str) -> bool:
    """Return True if *name* is a registered primitive or export alias."""
    return name in _ALL_PRIMITIVES


def get_all_primitives() -> frozenset[str]:
    """Return the full set of registered primitive names (base + aliases)."""
    return _ALL_PRIMITIVES
