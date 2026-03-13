"""Unit tests for dependency_graph_builder — topological sort and circular dependency."""
from __future__ import annotations

import pytest


def test_topological_ordering_respects_composed_of():
    """Pressable and Text must appear before Button in the sorted order."""
    from daf.tools.dependency_graph_builder import build_dependency_graph, topological_sort

    specs = {
        "Button": {"composedOf": ["Pressable", "Text"]},
        "Pressable": {},
        "Text": {},
    }
    graph = build_dependency_graph(specs)
    order = topological_sort(graph)

    assert order.index("Pressable") < order.index("Button")
    assert order.index("Text") < order.index("Button")


def test_circular_dependency_raises_error():
    """Circular dependency between CompA and CompB raises CircularDependencyError."""
    from daf.tools.dependency_graph_builder import build_dependency_graph, CircularDependencyError

    specs = {
        "CompA": {"composedOf": ["CompB"]},
        "CompB": {"composedOf": ["CompA"]},
    }
    with pytest.raises(CircularDependencyError):
        graph = build_dependency_graph(specs)
        from daf.tools.dependency_graph_builder import topological_sort
        topological_sort(graph)
