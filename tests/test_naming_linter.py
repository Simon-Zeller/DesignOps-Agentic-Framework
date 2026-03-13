"""Unit tests for NamingLinter tool — TDD red phase."""
from __future__ import annotations

import pytest


def test_clean_names_return_empty_violations():
    """Well-formed kebab-case keys with valid prefixes produce no violations."""
    from daf.tools.naming_linter import NamingLinter

    keys = [
        "color.brand.primary",
        "color.brand.secondary",
        "scale.spacing.4",
        "text.default",
        "surface.elevated",
    ]
    result = NamingLinter()._run(keys=keys)
    assert result["fatal"] == []
    assert result["warnings"] == []


def test_blocked_abbreviation_produces_warning():
    """'bg' is a blocked abbreviation — produces one warning entry."""
    from daf.tools.naming_linter import NamingLinter

    keys = ["color.bg.primary"]
    result = NamingLinter()._run(keys=keys)
    assert result["fatal"] == []
    assert len(result["warnings"]) >= 1
    details = " ".join(w.get("detail", "") for w in result["warnings"])
    assert "bg" in details.lower() or "abbreviation" in details.lower()


def test_camel_case_produces_fatal_violation():
    """camelCase key produces a fatal violation (wrong casing)."""
    from daf.tools.naming_linter import NamingLinter

    keys = ["colorBrandPrimary"]
    result = NamingLinter()._run(keys=keys)
    assert len(result["fatal"]) >= 1
