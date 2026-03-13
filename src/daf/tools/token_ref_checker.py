"""Token Reference Checker — resolves token references in spec against compiled tokens."""
from __future__ import annotations

from typing import Any


def check_token_refs(
    spec_tokens: dict[str, str],
    compiled_tokens: dict[str, Any],
) -> dict[str, Any]:
    """Check whether all token values in *spec_tokens* exist in *compiled_tokens*.

    Args:
        spec_tokens: Mapping of prop name → token path (e.g. ``{"background": "color.brand.primary"}``).
        compiled_tokens: Flat dict of resolved token paths → values.

    Returns:
        ``{"unresolved": [...], "all_resolved": bool}``
    """
    if not spec_tokens:
        return {"unresolved": [], "all_resolved": True}

    unresolved: list[str] = []
    for _prop, token_path in spec_tokens.items():
        if isinstance(token_path, str) and token_path not in compiled_tokens:
            unresolved.append(token_path)

    return {
        "unresolved": unresolved,
        "all_resolved": len(unresolved) == 0,
    }
