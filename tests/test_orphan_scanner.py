"""Unit tests for OrphanScanner tool — TDD red phase."""
from __future__ import annotations

import pytest


def test_referenced_token_not_flagged_as_orphan():
    """A global token that is referenced by a semantic token is not orphaned."""
    from daf.tools.orphan_scanner import OrphanScanner

    graph = {
        "color.brand.primary": [],            # base token, no outgoing refs
        "color.interactive.default": ["color.brand.primary"],  # references base
    }
    orphans = OrphanScanner()._run(graph=graph)
    assert "color.brand.primary" not in orphans


def test_unreferenced_global_token_flagged_as_orphan():
    """A global token that nothing references appears in orphan list."""
    from daf.tools.orphan_scanner import OrphanScanner

    graph = {
        "color.brand.primary": [],
        "color.neutral.050": [],              # defined but never referenced
        "color.interactive.default": ["color.brand.primary"],
    }
    orphans = OrphanScanner()._run(graph=graph)
    assert "color.neutral.050" in orphans


def test_all_orphaned_tokens_emit_multiple_entries():
    """When no references exist, all tokens are orphaned."""
    from daf.tools.orphan_scanner import OrphanScanner

    graph = {
        "color.brand.primary": [],
        "color.brand.secondary": [],
        "color.neutral.050": [],
    }
    orphans = OrphanScanner()._run(graph=graph)
    assert set(orphans) == {"color.brand.primary", "color.brand.secondary", "color.neutral.050"}
