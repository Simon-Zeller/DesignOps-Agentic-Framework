"""BrandProfileSchemaValidator — validates brand-profile.json against the §6 JSON Schema."""
from __future__ import annotations

import copy
import re
from typing import Any

import jsonschema
from crewai.tools import BaseTool

# ── §6 JSON Schema ────────────────────────────────────────────────────────────

# Color property: accepts #RGB, #RRGGBB, or any multi-word natural language string.
# Single-word, non-hex strings (like "red") are rejected.
_COLOR_PROPERTY: dict[str, Any] = {
    "type": "string",
    "anyOf": [
        {"pattern": "^#[0-9A-Fa-f]{3}$"},
        {"pattern": "^#[0-9A-Fa-f]{6}$"},
        {"pattern": "\\s"},  # natural language: must contain whitespace
    ],
}

BRAND_PROFILE_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "archetype"],
    "additionalProperties": True,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "archetype": {
            "type": "string",
            "enum": [
                "enterprise-b2b",
                "consumer-b2c",
                "mobile-first",
                "multi-brand",
                "custom",
            ],
        },
        "colors": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "primary": copy.deepcopy(_COLOR_PROPERTY),
                "secondary": copy.deepcopy(_COLOR_PROPERTY),
                "accent": copy.deepcopy(_COLOR_PROPERTY),
                "neutral": copy.deepcopy(_COLOR_PROPERTY),
                "background": copy.deepcopy(_COLOR_PROPERTY),
                "surface": copy.deepcopy(_COLOR_PROPERTY),
                "text": copy.deepcopy(_COLOR_PROPERTY),
            },
        },
        "typography": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "scaleRatio": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 2.0,
                },
                "baseSize": {
                    "type": "integer",
                    "minimum": 8,
                    "maximum": 24,
                },
            },
        },
        "spacing": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "density": {"type": "string"},
                "baseUnit": {"type": "number"},
            },
        },
        "borderRadius": {"type": "string"},
        "elevation": {"type": "string"},
        "motion": {"type": "string"},
        "themes": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "modes": {"type": "array", "items": {"type": "string"}},
                "brandOverrides": {"type": "boolean"},
            },
        },
        "accessibility": {"type": "string"},
        "componentScope": {"type": "string"},
        "breakpoints": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "strategy": {"type": "string"},
            },
        },
    },
}

# Known color sub-property names (used to detect anyOf errors for colors)
_COLOR_FIELD_NAMES: frozenset[str] = frozenset(
    {"primary", "secondary", "accent", "neutral", "background", "surface", "text"}
)


class BrandProfileSchemaValidator(BaseTool):
    """Validates a brand profile dict against the §6 JSON Schema.

    Returns ``{"valid": bool, "errors": [{"field": str, "message": str}]}``.
    """

    name: str = "brand_profile_schema_validator"
    description: str = (
        "Validates a raw brand profile dict against the §6 brand profile JSON Schema. "
        "Returns a structured result with valid flag and field-level error list."
    )

    def _run(self, profile: dict[str, Any]) -> dict[str, Any]:
        validator = jsonschema.Draft7Validator(BRAND_PROFILE_SCHEMA)
        errors = []
        for error in validator.iter_errors(profile):
            field, message = self._extract_field_and_message(error)
            errors.append({"field": field, "message": message})
        return {"valid": len(errors) == 0, "errors": errors}

    # ── helpers ───────────────────────────────────────────────────────────────

    def _extract_field_and_message(
        self, error: jsonschema.ValidationError
    ) -> tuple[str, str]:
        path = list(error.absolute_path)

        if error.validator == "required":
            m = re.search(r"'([^']+)' is a required property", error.message)
            field = m.group(1) if m else "root"
            return field, "Required field missing"

        field = ".".join(str(p) for p in path) if path else "root"

        if error.validator == "anyOf":
            # anyOf is used exclusively for color properties in this schema
            return field, "Invalid hex color: must be #RGB or #RRGGBB"

        if error.validator == "enum":
            allowed = ", ".join(f'"{v}"' for v in error.validator_value)
            return field, f"Invalid value; must be one of: {allowed}"

        if error.validator == "minimum":
            return (
                field,
                f"Value {error.instance} is below minimum {error.validator_value}",
            )

        if error.validator == "maximum":
            return (
                field,
                f"Value {error.instance} exceeds maximum {error.validator_value}",
            )

        return field, error.message
