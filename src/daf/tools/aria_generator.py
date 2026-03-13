"""ARIA Generator — maps component types and states to ARIA attribute patch instructions.

Uses a rule table to produce concrete patch instructions without LLM calls.
"""
from __future__ import annotations

from typing import Any

# Rule table: component_type → list of patch instruction templates
# Each patch: {"attribute": str, "value": str | None, "binding": str | None, "element": str}
_ARIA_RULES: dict[str, list[dict[str, Any]]] = {
    "button": [
        {"attribute": "aria-disabled", "binding": "disabled", "element": "root", "condition": "has_disabled_state"},
        {"attribute": "aria-pressed", "binding": "pressed", "element": "root", "condition": "has_pressed_state"},
        {"attribute": "aria-expanded", "binding": "expanded", "element": "root", "condition": "has_expanded_state"},
    ],
    "dialog": [
        {"attribute": "role", "value": "dialog", "element": "root"},
        {"attribute": "aria-modal", "value": "true", "element": "root"},
        {"attribute": "aria-labelledby", "binding": "titleId", "element": "root", "condition": "has_title"},
    ],
    "alertdialog": [
        {"attribute": "role", "value": "alertdialog", "element": "root"},
        {"attribute": "aria-modal", "value": "true", "element": "root"},
    ],
    "status": [
        {"attribute": "aria-live", "value": "polite", "element": "root"},
        {"attribute": "aria-atomic", "value": "true", "element": "root"},
    ],
    "alert": [
        {"attribute": "aria-live", "value": "assertive", "element": "root"},
        {"attribute": "aria-atomic", "value": "true", "element": "root"},
    ],
    "listbox": [
        {"attribute": "role", "value": "listbox", "element": "root"},
        {"attribute": "aria-multiselectable", "binding": "multiSelect", "element": "root", "condition": "has_multi_select"},
    ],
    "combobox": [
        {"attribute": "role", "value": "combobox", "element": "input"},
        {"attribute": "aria-expanded", "binding": "isOpen", "element": "input"},
        {"attribute": "aria-haspopup", "value": "listbox", "element": "input"},
    ],
    "tab": [
        {"attribute": "role", "value": "tab", "element": "root"},
        {"attribute": "aria-selected", "binding": "isSelected", "element": "root"},
    ],
    "tabpanel": [
        {"attribute": "role", "value": "tabpanel", "element": "root"},
        {"attribute": "aria-labelledby", "binding": "tabId", "element": "root"},
    ],
    "checkbox": [
        {"attribute": "aria-checked", "binding": "checked", "element": "root"},
        {"attribute": "aria-disabled", "binding": "disabled", "element": "root", "condition": "has_disabled_state"},
    ],
    "switch": [
        {"attribute": "role", "value": "switch", "element": "root"},
        {"attribute": "aria-checked", "binding": "on", "element": "root"},
    ],
}


def _has_state(spec: dict[str, Any], state_name: str) -> bool:
    """Return True if *state_name* is present in the spec states."""
    states = spec.get("states", {})
    if isinstance(states, dict):
        return state_name in states
    if isinstance(states, list):
        return state_name in states
    return False


def generate_aria_patches(
    spec: dict[str, Any],
    component_type: str,
) -> list[dict[str, Any]]:
    """Generate ARIA attribute patch instructions for *component_type*.

    Args:
        spec: The component spec dict (for state introspection).
        component_type: One of the supported ARIA roles (e.g. ``"button"``, ``"dialog"``).

    Returns:
        List of patch instruction dicts, each containing ``attribute`` and either
        ``value`` (literal) or ``binding`` (prop name to bind dynamically).
    """
    rules = _ARIA_RULES.get(component_type.lower(), [])
    patches: list[dict[str, Any]] = []

    for rule in rules:
        condition = rule.get("condition")
        # Apply condition checks
        if condition == "has_disabled_state" and not _has_state(spec, "disabled"):
            continue
        if condition == "has_pressed_state" and not _has_state(spec, "pressed"):
            continue
        if condition == "has_expanded_state" and not (
            _has_state(spec, "expanded") or _has_state(spec, "open")
        ):
            continue
        if condition == "has_title":
            pass  # include by default for dialog
        if condition == "has_multi_select":
            continue  # skip optional multi-select

        patch: dict[str, Any] = {"attribute": rule["attribute"], "element": rule.get("element", "root")}
        if "value" in rule:
            patch["value"] = rule["value"]
        if "binding" in rule:
            patch["binding"] = rule["binding"]
        patches.append(patch)

    return patches
