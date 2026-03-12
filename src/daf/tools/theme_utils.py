"""Shared theme utility helpers (p05).

Extracted from style_dictionary_compiler and validator to eliminate duplication.
"""
from __future__ import annotations

import re
from typing import Any

ALIAS_INNER_RE = re.compile(r"^\{([a-z0-9._-]+)\}$")
DTCG_ALIAS_RE = re.compile(r"^\{[a-z0-9._-]+\}$")


def walk_tokens(
    data: dict[str, Any],
    path: str = "",
) -> list[tuple[str, dict[str, Any]]]:
    """Yield (dot-path, token_dict) for every leaf token in a nested DTCG dict."""
    results = []
    for key, val in data.items():
        if key.startswith("$"):
            continue
        current = f"{path}.{key}" if path else key
        if isinstance(val, dict):
            if "$value" in val:
                results.append((current, val))
            else:
                results.extend(walk_tokens(val, current))
    return results
