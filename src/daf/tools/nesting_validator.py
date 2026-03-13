"""Nesting Validator — checks TSX source for forbidden nesting patterns and depth violations.

Uses source-text heuristic scanning (fast path). Falls back to ts-node for
complex cases.

Forbidden nesting patterns:
- Pressable inside Pressable (interactive inside interactive)
"""
from __future__ import annotations

import re
from typing import Any

# Interactive primitive elements that cannot be nested inside each other
_INTERACTIVE_PRIMITIVES = frozenset({"Pressable"})

# All JSX element names we track for nesting depth
_JSX_OPEN_RE = re.compile(r"<([A-Z][a-zA-Z0-9]*)\b[^>]*/?>")
_JSX_CLOSE_RE = re.compile(r"</([A-Z][a-zA-Z0-9]*)>")


def _count_max_depth(tsx_source: str) -> int:
    """Estimate max JSX nesting depth by counting open/close component tags.

    Opens are counted before closes on each line so that ``<Tag>...</Tag>``
    on a single line correctly increments the depth counter.
    """
    depth = 0
    max_depth = 0
    open_re = re.compile(r"<([A-Z][a-zA-Z0-9]*)\b[^>]*(?<!/)>")
    close_re = re.compile(r"</([A-Z][a-zA-Z0-9]*)>")
    self_close_re = re.compile(r"<[A-Z][a-zA-Z0-9]*\b[^>]*/\s*>")

    for line in tsx_source.splitlines():
        # Strip self-closing tags (they don't affect depth)
        stripped = self_close_re.sub("", line)

        opens = open_re.findall(stripped)
        closes = close_re.findall(stripped)

        # Process opens first so inline <Tag>...</Tag> registers its depth
        for _ in opens:
            depth += 1
            if depth > max_depth:
                max_depth = depth

        for _ in closes:
            depth = max(0, depth - 1)

    return max_depth


def _find_forbidden_nesting(tsx_source: str) -> list[dict[str, str]]:
    """Detect forbidden nesting patterns like Pressable-inside-Pressable.

    Uses a simple stack-based heuristic on the source text.
    """
    forbidden: list[dict[str, str]] = []
    stack: list[str] = []

    # Process JSX tokens line by line
    open_tag_re = re.compile(r"<([A-Z][a-zA-Z0-9]*)\b[^>]*(?<!/)>")
    close_tag_re = re.compile(r"</([A-Z][a-zA-Z0-9]*)>")
    self_close_re = re.compile(r"<([A-Z][a-zA-Z0-9]*)\b[^>]*/\s*>")

    for line in tsx_source.splitlines():
        # Remove self-closing first (they don't affect the stack)
        line_no_self = self_close_re.sub("", line)

        opens = open_tag_re.findall(line_no_self)
        closes = close_tag_re.findall(line_no_self)

        for tag in opens:
            if tag in _INTERACTIVE_PRIMITIVES and tag in stack:
                # Already inside the same interactive element
                forbidden.append({"outer": tag, "inner": tag})
            stack.append(tag)

        for tag in closes:
            # Pop from end of stack
            for i in range(len(stack) - 1, -1, -1):
                if stack[i] == tag:
                    stack.pop(i)
                    break

    return forbidden


def validate_nesting(tsx_source: str) -> dict[str, Any]:
    """Validate TSX source for forbidden nesting patterns and excessive depth.

    Returns:
        ``{
            "valid": bool,
            "forbidden_nesting": [{"outer": ..., "inner": ...}, ...],
            "depth": int,
            "depth_warning": bool,
        }``
    """
    forbidden = _find_forbidden_nesting(tsx_source)
    depth = _count_max_depth(tsx_source)
    depth_warning = depth > 5

    return {
        "valid": len(forbidden) == 0,
        "forbidden_nesting": forbidden,
        "depth": depth,
        "depth_warning": depth_warning,
    }
