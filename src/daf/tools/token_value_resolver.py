"""Tool: token_value_resolver — resolves token values and classifies tiers."""
from __future__ import annotations


def resolve_token(token_path: str, compiled_tokens: dict[str, str]) -> str | None:
    """Look up a token path in the compiled token map.

    Args:
        token_path: Dot-separated token path (e.g. ``"color.interactive.default"``).
        compiled_tokens: Flat dict of token path → resolved value.

    Returns:
        The resolved value string, or ``None`` if not found.
    """
    return compiled_tokens.get(token_path)


def classify_tier(token_path: str) -> str:
    """Classify a token into global, semantic, or component tier.

    Classification heuristics (checked in order):
    - If the second segment is ``"global"`` → ``"global"``
    - If the first segment is a known design-system primitive category
      (``color``, ``space``, ``typography``, ``radius``, ``shadow``)
      and the second segment is NOT ``"global"`` → ``"semantic"``
    - Everything else → ``"component"``

    Args:
        token_path: Dot-separated token path.

    Returns:
        One of ``"global"``, ``"semantic"``, or ``"component"``.
    """
    parts = token_path.split(".")

    if len(parts) >= 2 and parts[1] == "global":
        return "global"

    semantic_roots = {"color", "space", "typography", "radius", "shadow", "font"}
    if parts[0] in semantic_roots:
        return "semantic"

    return "component"
