"""Scope Analyzer — classifies components as primitive / simple / complex."""
from __future__ import annotations

_PRIMITIVE_NAMES = frozenset({
    "Box", "Text", "Image", "Icon", "Spacer", "Divider", "Surface",
    "Pressable", "Stack", "Grid", "Flex",
})

_COMPLEX_VARIANT_THRESHOLD = 4


def classify_component(spec: dict) -> str:
    """Classify a component spec as 'primitive', 'simple', or 'complex'.

    Rules (applied in order):
    1. Known primitive name → ``"primitive"``
    2. ≥ complex_threshold variants → ``"complex"``
    3. Otherwise → ``"simple"``
    """
    name = spec.get("component", "")
    variants = spec.get("variants", [])

    if name in _PRIMITIVE_NAMES:
        return "primitive"
    if len(variants) >= _COMPLEX_VARIANT_THRESHOLD:
        return "complex"
    return "simple"
