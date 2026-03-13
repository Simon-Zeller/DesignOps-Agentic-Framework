"""Tool: usage_context_extractor — reverse-looks up a token path in a spec's tokens map."""
from __future__ import annotations


def extract_usage_context(token_path: str, spec_tokens_map: dict[str, str]) -> str:
    """Return the role name for a token path by reverse-looking it up in a spec map.

    Args:
        token_path: Dot-separated token path to look up.
        spec_tokens_map: Dict mapping role name → token path
            (e.g. ``{"background": "color.interactive.default"}``).

    Returns:
        The role name string if found, or an empty string if not found.
        Never raises.
    """
    for role, path in spec_tokens_map.items():
        if path == token_path:
            return role
    return ""
