"""Unit tests for priority_queue_builder — primitive-first queue ordering."""
from __future__ import annotations


def test_primitives_precede_simple_precede_complex():
    """Queue must be ordered primitive → simple → complex."""
    from daf.tools.priority_queue_builder import build_priority_queue

    classified = [
        {"name": "DataGrid", "tier": "complex"},
        {"name": "Button", "tier": "simple"},
        {"name": "Box", "tier": "primitive"},
    ]
    topo_order = ["Box", "Button", "DataGrid"]
    queue = build_priority_queue(classified, topo_order)

    tiers = [item["tier"] for item in queue]
    # All primitives come first, then simple, then complex
    assert tiers.index("primitive") < tiers.index("simple")
    assert tiers.index("simple") < tiers.index("complex")
