"""Structural validator for brand profiles (§13.3 rules).

Validates the structural correctness of a brand profile dict.
Semantic validation (contradiction detection, enrichment) is handled
by the Brand Discovery Agent (P03).
"""

import re
from typing import Any

VALID_ARCHETYPES = frozenset(
    {"enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand", "custom"}
)

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _is_valid_hex(value: str) -> bool:
    """Return True if *value* is a valid 3- or 6-digit hex color."""
    return bool(_HEX_RE.match(value))


def _is_natural_language(value: str) -> bool:
    """Return True if *value* looks like a natural language description.

    A value is considered natural language if it contains at least one space,
    indicating it is a descriptive phrase rather than a color keyword or code.
    Empty strings and single-word CSS keywords are NOT natural language.
    """
    return " " in value


def _validate_color_value(value: str, field_path: str, errors: list[str]) -> None:
    """Validate a single color field value, appending errors to *errors*."""
    if not value:
        errors.append(f"{field_path}: color value is required")
        return
    if value.startswith("#"):
        if not _is_valid_hex(value):
            errors.append(
                f"{field_path}: invalid hex color — must be 3 or 6 hex digits"
                f" (e.g., #FF0000), got {value!r}"
            )
    elif not _is_natural_language(value):
        # Single-word non-hex values (CSS keywords, typos) are rejected
        errors.append(
            f"{field_path}: invalid color value — use a hex code (#RRGGBB) or"
            f" a natural language description (e.g., 'a warm coral red'),"
            f" got {value!r}"
        )
    # Multi-word natural language descriptions ("%s words") are accepted verbatim


def validate_profile(data: dict[str, Any]) -> list[str]:
    """Validate *data* against the §13.3 structural rules.

    Returns a list of human-readable error strings.  An empty list means
    the profile is structurally valid.
    """
    errors: list[str] = []

    # --- name ---
    name = data.get("name", "")
    if not name or not str(name).strip():
        errors.append("name: required — cannot be empty or whitespace-only")

    # --- archetype ---
    archetype = data.get("archetype", "")
    if archetype not in VALID_ARCHETYPES:
        valid = ", ".join(sorted(VALID_ARCHETYPES))
        errors.append(f"archetype: must be one of [{valid}], got {archetype!r}")

    # --- colors ---
    colors = data.get("colors", {})
    if isinstance(colors, dict):
        for field in ("primary", "secondary", "neutral"):
            value = colors.get(field)
            if value is not None:
                _validate_color_value(str(value), f"colors.{field}", errors)

        semantic = colors.get("semantic", {})
        if isinstance(semantic, dict):
            for field in ("success", "warning", "error", "info"):
                value = semantic.get(field)
                if value is not None:
                    _validate_color_value(
                        str(value), f"colors.semantic.{field}", errors
                    )

    # --- typography ---
    typography = data.get("typography", {})
    if isinstance(typography, dict):
        scale_ratio = typography.get("scaleRatio")
        if scale_ratio is not None:
            try:
                ratio_f = float(scale_ratio)
                if not (1.0 <= ratio_f <= 2.0):
                    errors.append(
                        f"typography.scaleRatio: must be between 1.0 and 2.0,"
                        f" got {scale_ratio}"
                    )
            except (TypeError, ValueError):
                errors.append(
                    f"typography.scaleRatio: must be a number, got {scale_ratio!r}"
                )

        base_size = typography.get("baseSize")
        if base_size is not None:
            try:
                size_i = int(base_size)
                if not (8 <= size_i <= 24):
                    errors.append(
                        f"typography.baseSize: must be between 8 and 24,"
                        f" got {base_size}"
                    )
            except (TypeError, ValueError):
                errors.append(
                    f"typography.baseSize: must be an integer, got {base_size!r}"
                )

    return errors
