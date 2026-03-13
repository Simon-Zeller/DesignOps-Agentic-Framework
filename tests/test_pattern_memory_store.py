"""Unit tests for pattern_memory_store — store/retrieve and empty-return."""
from __future__ import annotations


def test_stores_and_retrieves_prop_shapes():
    """Stored pattern for Card can be retrieved when querying CardHeader."""
    from daf.tools.pattern_memory_store import PatternMemoryStore

    store = PatternMemoryStore()
    store.store_pattern("Card", {"padding": "SpacingToken", "elevation": "ShadowToken"})

    results = store.retrieve_similar_patterns("CardHeader")

    assert len(results) > 0
    # The Card pattern should be in the results
    names = [r.get("name") or r.get("component") for r in results]
    assert "Card" in names


def test_returns_empty_on_no_matching_patterns():
    """Empty store returns [] without raising."""
    from daf.tools.pattern_memory_store import PatternMemoryStore

    store = PatternMemoryStore()
    results = store.retrieve_similar_patterns("NewComponent")

    assert results == []
