"""Tool: scale_visualizer — produces human-readable visual representations of token values."""
from __future__ import annotations


def visualize_token(token_path: str, value: str) -> str:
    """Return a visual representation of a token value.

    Rules:
    - Color tokens (path contains ``color``) → ``■ {value}``
    - Spacing tokens (path starts with ``space``) → ``— {value}``
    - All other tokens → value as-is

    Args:
        token_path: Dot-separated token path.
        value: Resolved token value string.

    Returns:
        A display string for the token.
    """
    parts = token_path.split(".")
    root = parts[0] if parts else ""

    if "color" in token_path:
        return f"■ {value}"

    if root in {"space", "spacing"}:
        return f"— {value}"

    return value
