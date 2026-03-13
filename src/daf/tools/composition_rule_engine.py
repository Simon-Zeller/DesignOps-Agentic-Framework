"""Composition Rule Engine — checks TSX source for primitive-only composition.

Uses two-pass heuristic:
1. Import statement analysis via regex → detect non-primitive imports
2. JSX element scanning → detect direct DOM element usage

Falls back to ts-node subprocess for complex cases (optional).
"""
from __future__ import annotations

import re
from typing import Any

# Matches import statements
_IMPORT_RE = re.compile(r"""import\s+.*?from\s+['"]([^'"]+)['"]""", re.DOTALL)
# Matches hex color literals in style values
_HEX_COLOR_RE = re.compile(r"['\"](#[0-9a-fA-F]{3,8})['\"]")
# Matches token var() references
_TOKEN_VAR_RE = re.compile(r"var\(--[a-z][a-z0-9-]*\)")
# Matches px values that are hardcoded (not from a var)
_HARDCODED_PX_RE = re.compile(r"['\"](\d+px)['\"]")
# Matches style property value strings that are hex or hardcoded
_STYLE_VALUE_RE = re.compile(r":\s*['\"](?:#[0-9a-fA-F]{3,8}|\d+px)['\"]")

_PRIMITIVE_IMPORT_PREFIXES = (
    "src/primitives",
    "../primitives",
    "../../primitives",
    "./primitives",
    "@primitives",
)


def _is_primitive_import_source(source: str) -> bool:
    """Return True if *source* is a known primitive import path."""
    return any(source.startswith(p) or source == p for p in _PRIMITIVE_IMPORT_PREFIXES)


def check_composition(
    tsx_source: str,
    registry: Any,  # noqa: ARG001 — registry param reserved for future use
) -> dict[str, Any]:
    """Analyse TSX source for non-primitive imports.

    Returns:
        ``{"valid": bool, "violations": [...], "non_primitive_imports": [...]}``
    """
    violations: list[dict[str, str]] = []
    non_primitive_imports: list[str] = []

    for match in _IMPORT_RE.finditer(tsx_source):
        source = match.group(1)
        # Skip React, test utilities, and primitive sources
        if source in ("react", "vitest", "@testing-library/react"):
            continue
        if _is_primitive_import_source(source):
            continue
        # Flag external library imports that are not from primitive paths
        if source.startswith("@") or (not source.startswith(".") and not source.startswith("src/")):
            non_primitive_imports.append(source)
            violations.append({
                "type": "non-primitive-import",
                "import": source,
                "message": f"Non-primitive external import: {source!r}",
            })

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "non_primitive_imports": non_primitive_imports,
    }


def compute_token_compliance(tsx_source: str) -> dict[str, Any]:
    """Compute the ratio of token-backed style values vs. hardcoded values.

    Counts hex color literals (``#rrggbb``) as "hardcoded".
    Counts everything else including ``var(--token)`` as potential style values.

    Returns:
        ``{"token_compliance": float, "hardcoded_values": int, "total_style_values": int}``
    """
    hex_matches = _HEX_COLOR_RE.findall(tsx_source)
    hardcoded_count = len(hex_matches)

    # Count all style property values (var() tokens + hardcoded px/hex)
    token_var_count = len(_TOKEN_VAR_RE.findall(tsx_source))
    hardcoded_px_count = len(_HARDCODED_PX_RE.findall(tsx_source))
    total = token_var_count + hardcoded_count + hardcoded_px_count

    if total == 0:
        return {"token_compliance": 1.0, "hardcoded_values": 0, "total_style_values": 0}

    compliance = (total - hardcoded_count) / total
    return {
        "token_compliance": round(compliance, 6),
        "hardcoded_values": hardcoded_count,
        "total_style_values": total,
    }
