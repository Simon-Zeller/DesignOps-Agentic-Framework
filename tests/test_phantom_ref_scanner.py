"""Unit tests for PhantomRefScanner tool — TDD red phase."""
from __future__ import annotations

import pytest


def test_valid_references_return_empty_list():
    """All references resolve to existing keys — no phantoms."""
    from daf.tools.phantom_ref_scanner import PhantomRefScanner

    merged_namespace = {
        "color.brand.primary",
        "color.interactive.default",
    }
    references = {
        "color.interactive.default": "color.brand.primary",
    }
    result = PhantomRefScanner()._run(
        merged_namespace=merged_namespace,
        references=references,
    )
    assert result == []


def test_detects_missing_reference_target():
    """A reference to a non-existent key produces a phantom entry."""
    from daf.tools.phantom_ref_scanner import PhantomRefScanner

    merged_namespace = {
        "color.brand.primary",
    }
    references = {
        "color.interactive.default": "color.brand.nonexistent",  # doesn't exist
    }
    result = PhantomRefScanner()._run(
        merged_namespace=merged_namespace,
        references=references,
    )
    assert len(result) >= 1
    entry = result[0]
    assert "token_path" in entry
    assert "missing_ref" in entry
    assert entry["missing_ref"] == "color.brand.nonexistent"
