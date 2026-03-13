"""NamingLinter — CrewAI BaseTool.

Enforces DAF token naming conventions:
- All-lowercase kebab-case segments separated by dots
- No camelCase or PascalCase segments
- No blocked abbreviations

Returns {fatal: list, warnings: list}.
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Blocked abbreviations — per PRD §4.2 naming guidance
# ---------------------------------------------------------------------------

BLOCKED_ABBREVIATIONS: frozenset[str] = frozenset({
    "bg",    # use "background"
    "fg",    # use "foreground"
    "txt",   # use "text"
    "btn",   # use "button"
    "clr",   # use "color"
    "sz",    # use "size"
    "ht",    # use "height"
    "wt",    # use "width"
    "pos",   # use "position"
    "num",   # use "number"
    "str",   # use "string"
    "img",   # use "image"
    "ico",   # use "icon"
    "fnt",   # use "font"
    "bdr",   # use "border"
    "rad",   # use "radius"
    "spc",   # use "spacing"
    "opac",  # use "opacity"
    "dur",   # use "duration"
    "anim",  # use "animation"
})

# Kebab-case segment: lowercase letters/digits, optional hyphens; digit-only segments allowed
_VALID_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9]*(?:-[a-z0-9]+)*$")
# camelCase detector: any uppercase letter preceded by a lowercase letter or digit
_CAMEL_CASE_RE = re.compile(r"[a-z0-9][A-Z]")


class _LinterInput(BaseModel):
    keys: list[str]


class NamingLinter(BaseTool):
    """Enforce DAF token naming conventions on a list of dot-path token keys."""

    name: str = "naming_linter"
    description: str = (
        "Validate a list of dot-path token keys against DAF naming conventions. "
        "Returns {fatal: list, warnings: list}."
    )
    args_schema: type[BaseModel] = _LinterInput

    def _run(self, keys: list[str], **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        fatal: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        for key in keys:
            # Check for camelCase — fatal
            if _CAMEL_CASE_RE.search(key) or (key and key[0].isupper()):
                fatal.append({
                    "check": "naming_convention",
                    "severity": "fatal",
                    "token_path": key,
                    "detail": f"Token key '{key}' uses wrong casing (camelCase/PascalCase). Use lowercase kebab-case dot-path.",
                    "suggestion": "Use all-lowercase dot-separated segments, e.g. 'color.brand.primary'.",
                })
                continue  # Skip further checks if fatal casing issue

            # Validate each segment
            segments = key.split(".")
            for segment in segments:
                if not _VALID_SEGMENT_RE.match(segment):
                    fatal.append({
                        "check": "naming_convention",
                        "severity": "fatal",
                        "token_path": key,
                        "detail": f"Segment '{segment}' in key '{key}' does not match kebab-case convention.",
                        "suggestion": "Use only lowercase letters, digits, and hyphens.",
                    })

                if segment in BLOCKED_ABBREVIATIONS:
                    warnings.append({
                        "check": "naming_convention",
                        "severity": "warning",
                        "token_path": key,
                        "detail": f"Token key '{key}' contains blocked abbreviation: {segment}. Use the full word instead.",
                        "suggestion": f"Replace '{segment}' with its full form.",
                    })

        return {"fatal": fatal, "warnings": warnings}
