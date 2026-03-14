"""Tool: spec_to_doc_renderer — extracts doc sections from a component spec dict."""
from __future__ import annotations

from typing import Any


def render_spec_to_sections(spec_dict: dict[str, Any]) -> dict[str, Any]:
    """Extract structured documentation sections from a component spec.

    Args:
        spec_dict: A parsed component spec (from ``*.spec.yaml``).

    Returns:
        A dict with keys: ``name``, ``props``, ``variants``, ``token_bindings``.
    """
    name: str = spec_dict.get("component", "")

    raw_props: dict[str, Any] = spec_dict.get("props", {}) or {}
    props: list[dict[str, Any]] = []
    for prop_name, meta in raw_props.items():
        if not isinstance(meta, dict):
            meta = {}
        props.append(
            {
                "name": prop_name,
                "type": meta.get("type", "any"),
                "required": bool(meta.get("required", False)),
                "default": meta.get("default", None),
                "description": meta.get("description", ""),
            }
        )

    variants: list[str] = list(spec_dict.get("variants", []) or [])

    # Support both "tokens" (dict) and "tokenBindings" (list of {prop, $value})
    token_bindings: dict[str, str] = {}
    raw_tokens = spec_dict.get("tokens")
    if isinstance(raw_tokens, dict):
        token_bindings = dict(raw_tokens)

    raw_bindings = spec_dict.get("tokenBindings")
    if isinstance(raw_bindings, list):
        for binding in raw_bindings:
            if isinstance(binding, dict):
                prop = binding.get("prop", "")
                val = binding.get("$value", "")
                if prop and val:
                    token_bindings[prop] = val

    return {
        "name": name,
        "props": props,
        "variants": variants,
        "token_bindings": token_bindings,
    }
