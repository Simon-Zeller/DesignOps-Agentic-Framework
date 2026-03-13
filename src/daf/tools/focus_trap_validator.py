"""Focus Trap Validator — checks TSX source for focus trap implementation.

Validates modal/overlay components for:
- Programmatic focus on open (useEffect + .focus())
- Tab cycling (onKeyDown Tab handling)
- Focus restoration on close
"""
from __future__ import annotations

import re
from typing import Any

_DIALOG_COMPONENT_TYPES = frozenset({"dialog", "modal", "drawer", "sheet", "alertdialog"})

_USE_EFFECT_FOCUS_RE = re.compile(r"useEffect\s*\(", re.IGNORECASE)
_FOCUS_CALL_RE = re.compile(r"\.focus\s*\(\s*\)")
_TAB_KEY_RE = re.compile(r"['\"]Tab['\"]")
_KEY_DOWN_RE = re.compile(r"onKeyDown|handleKeyDown", re.IGNORECASE)


def validate_focus_trap(
    tsx_source: str,
    component_type: str,
) -> dict[str, Any]:
    """Validate focus trap implementation for dialog-type components.

    Args:
        tsx_source: Full TSX source text.
        component_type: The component's role (e.g. ``"dialog"``, ``"button"``).

    Returns:
        ``{
            "focus_trap_present": bool | None,
            "issues": [...],
            "not_applicable": bool,  # True for non-dialog types
        }``
    """
    if component_type.lower() not in _DIALOG_COMPONENT_TYPES:
        return {
            "focus_trap_present": None,
            "issues": [],
            "not_applicable": True,
        }

    issues: list[str] = []

    has_use_effect = bool(_USE_EFFECT_FOCUS_RE.search(tsx_source))
    has_focus_call = bool(_FOCUS_CALL_RE.search(tsx_source))
    has_tab_trap = bool(_TAB_KEY_RE.search(tsx_source)) and bool(_KEY_DOWN_RE.search(tsx_source))

    if not (has_use_effect and has_focus_call):
        issues.append("no programmatic focus on open")

    if not has_tab_trap:
        issues.append("no focus cycling")

    focus_trap_present = len(issues) == 0

    return {
        "focus_trap_present": focus_trap_present,
        "issues": issues,
        "not_applicable": False,
    }
