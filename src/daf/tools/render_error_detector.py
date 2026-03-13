"""Render Error Detector — parses Playwright console output for React exceptions."""
from __future__ import annotations

import re
from typing import Any

_ERROR_PATTERNS: list[tuple[str, str]] = [
    (r"Error: (.+)", "react_exception"),
    (r"Uncaught (?:TypeError|ReferenceError|SyntaxError): (.+)", "react_exception"),
    (r"Warning: (.+) did not match", "hydration_warning"),
    (r"Warning: Each child in a list should have a unique", "key_warning"),
    (r"Cannot read propert(?:y|ies) of (.+)", "react_exception"),
    (r"React does not recognize the `\w+` prop", "unknown_prop"),
]


def detect_render_errors(console_log: str) -> list[dict[str, Any]]:
    """Scan *console_log* for React exceptions, render errors, and hydration warnings.

    Args:
        console_log: Raw string of Playwright console output.

    Returns:
        List of error dicts with ``type`` and ``message`` keys.
        Returns ``[]`` if no errors are detected.
    """
    errors: list[dict[str, Any]] = []

    for line in console_log.splitlines():
        for pattern, error_type in _ERROR_PATTERNS:
            match = re.search(pattern, line)
            if match:
                errors.append({
                    "type": error_type,
                    "message": match.group(1) if match.lastindex else line.strip(),
                })
                break  # one error per line

    return errors
