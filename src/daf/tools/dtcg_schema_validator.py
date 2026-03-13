"""DTCGSchemaValidator — CrewAI BaseTool.

Validates a nested DTCG token dictionary against the W3C DTCG specification
rules. Each leaf token must have $type and $value; extra fields produce
warnings. Returns {fatal: list, warnings: list}.
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# W3C DTCG recognised field names for leaf tokens
_DTCG_FIELDS = {"$type", "$value", "$description", "$extensions"}
_DTCG_TYPES = {
    "color", "dimension", "fontFamily", "fontWeight", "duration",
    "cubicBezier", "cubic-bezier", "number", "shadow", "gradient",
    "typography", "transition", "border", "other",
}


def _walk_leaf_tokens(
    data: dict[str, Any],
    path: str = "",
) -> list[tuple[str, dict[str, Any]]]:
    """Recursively yield (dot-path, token_obj) for every leaf token node."""
    results: list[tuple[str, dict[str, Any]]] = []
    for key, value in data.items():
        if key.startswith("$"):
            continue
        node_path = f"{path}.{key}" if path else key
        if isinstance(value, dict):
            if "$value" in value:
                results.append((node_path, value))
            else:
                results.extend(_walk_leaf_tokens(value, node_path))
    return results


class _ValidatorInput(BaseModel):
    token_dict: dict[str, Any]


class DTCGSchemaValidator(BaseTool):
    """Validate a DTCG token dict against W3C DTCG rules."""

    name: str = "dtcg_schema_validator"
    description: str = (
        "Validate a nested W3C DTCG token dictionary. "
        "Returns {fatal: list, warnings: list} where each entry has "
        "token_path, detail, check fields."
    )
    args_schema: type[BaseModel] = _ValidatorInput

    def _run(self, token_dict: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        fatal: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        leaf_tokens = _walk_leaf_tokens(token_dict)

        if not leaf_tokens:
            fatal.append({
                "check": "dtcg_schema",
                "severity": "fatal",
                "token_path": "<root>",
                "detail": "Token document contains no leaf tokens.",
                "suggestion": "Ensure the token document has at least one token with $value.",
            })
            return {"fatal": fatal, "warnings": warnings}

        for token_path, token_obj in leaf_tokens:
            if "$type" not in token_obj:
                fatal.append({
                    "check": "dtcg_schema",
                    "severity": "fatal",
                    "token_path": token_path,
                    "detail": f"Token '{token_path}' is missing required field '$type'.",
                    "suggestion": "Add '$type' field with a valid DTCG type.",
                })

            extra_fields = set(token_obj.keys()) - _DTCG_FIELDS
            for field in extra_fields:
                warnings.append({
                    "check": "dtcg_schema",
                    "severity": "warning",
                    "token_path": token_path,
                    "detail": f"Token '{token_path}' contains unrecognised field '{field}'.",
                    "suggestion": f"Remove or move '{field}' to $extensions.",
                })

        return {"fatal": fatal, "warnings": warnings}
