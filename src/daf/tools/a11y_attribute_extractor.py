"""A11y Attribute Extractor — maps spec-declared a11y requirements to ARIA attributes."""
from __future__ import annotations

from typing import Any

_ROLE_MAP: dict[str, dict[str, Any]] = {
    "button": {
        "attrs": ["aria-label", "aria-disabled"],
        "keyboard": ["Enter", "Space"],
    },
    "link": {
        "attrs": ["aria-label", "aria-current"],
        "keyboard": ["Enter"],
    },
    "checkbox": {
        "attrs": ["aria-checked", "aria-label", "aria-disabled"],
        "keyboard": ["Space"],
    },
    "radio": {
        "attrs": ["aria-checked", "aria-label", "aria-disabled"],
        "keyboard": ["Space", "ArrowUp", "ArrowDown"],
    },
    "listbox": {
        "attrs": ["aria-label", "aria-multiselectable"],
        "keyboard": ["ArrowUp", "ArrowDown", "Enter", "Space"],
    },
    "dialog": {
        "attrs": ["aria-label", "aria-modal", "aria-describedby"],
        "keyboard": ["Escape"],
    },
    "combobox": {
        "attrs": ["aria-expanded", "aria-haspopup", "aria-autocomplete", "aria-label"],
        "keyboard": ["ArrowUp", "ArrowDown", "Enter", "Escape"],
    },
    "tab": {
        "attrs": ["aria-selected", "aria-controls", "aria-label"],
        "keyboard": ["ArrowLeft", "ArrowRight", "Enter", "Space"],
    },
    "generic": {
        "attrs": [],
        "keyboard": [],
    },
}


def extract_a11y_attributes(spec: dict[str, Any]) -> dict[str, Any]:
    """Map spec-declared a11y role to ARIA attributes and keyboard handler stubs.

    Args:
        spec: Parsed component spec dict with optional ``a11y`` sub-dict.

    Returns:
        Dict with ``role``, ``attrs`` (list), and ``keyboard`` (list) keys.
    """
    a11y = spec.get("a11y") or {}
    role = a11y.get("role", "generic")
    mapping = _ROLE_MAP.get(role, _ROLE_MAP["generic"])

    return {
        "role": role,
        "attrs": list(mapping["attrs"]),
        "keyboard": list(mapping["keyboard"]),
    }
