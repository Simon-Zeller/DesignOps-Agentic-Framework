"""Unit tests for CircularRefDetector tool — TDD red phase."""
from __future__ import annotations

import pytest


def test_clean_dag_returns_no_cycles():
    """A valid DAG produces an empty list from cycle detection."""
    from daf.tools.circular_ref_detector import CircularRefDetector

    graph = {
        "color.brand.primary": [],
        "color.interactive.default": ["color.brand.primary"],
        "button.background": ["color.interactive.default"],
    }
    cycles = CircularRefDetector()._run(graph=graph)
    assert cycles == []


def test_detects_direct_cycle_a_b_a():
    """A → B → A returns one cycle entry containing the full path."""
    from daf.tools.circular_ref_detector import CircularRefDetector

    graph = {
        "token.a": ["token.b"],
        "token.b": ["token.a"],
    }
    cycles = CircularRefDetector()._run(graph=graph)
    assert len(cycles) >= 1
    # Each cycle entry should be a list/tuple of node names
    first_cycle = cycles[0]
    assert "token.a" in first_cycle
    assert "token.b" in first_cycle
