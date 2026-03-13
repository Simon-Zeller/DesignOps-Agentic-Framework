"""Unit tests for ReferenceGraphWalker tool — TDD red phase."""
from __future__ import annotations

import pytest


@pytest.fixture
def base_tokens():
    return {
        "color": {
            "brand": {
                "primary": {"$type": "color", "$value": "#005FCC"},
            }
        }
    }


@pytest.fixture
def semantic_tokens():
    return {
        "color": {
            "interactive": {
                "default": {"$type": "color", "$value": "{color.brand.primary}"},
            }
        }
    }


@pytest.fixture
def component_tokens():
    return {}


def test_flat_reference_list_for_simple_graph(base_tokens, semantic_tokens, component_tokens):
    """Graph contains one edge from semantic token to base token."""
    from daf.tools.reference_graph_walker import ReferenceGraphWalker

    graph = ReferenceGraphWalker()._run(
        base=base_tokens,
        semantic=semantic_tokens,
        component=component_tokens,
    )
    # Graph is an adjacency list: {source_path: [target_path, ...]}
    assert "color.interactive.default" in graph
    assert "color.brand.primary" in graph["color.interactive.default"]


def test_cross_file_reference_resolved_correctly():
    """Component → semantic → global chain: no phantom reference reported."""
    from daf.tools.reference_graph_walker import ReferenceGraphWalker

    base = {
        "color": {
            "brand": {
                "primary": {"$type": "color", "$value": "#005FCC"},
            }
        }
    }
    semantic = {
        "color": {
            "interactive": {
                "default": {"$type": "color", "$value": "{color.brand.primary}"},
            }
        }
    }
    component = {
        "button": {
            "background": {"$type": "color", "$value": "{color.interactive.default}"},
        }
    }
    graph = ReferenceGraphWalker()._run(base=base, semantic=semantic, component=component)
    assert "button.background" in graph
    assert "color.interactive.default" in graph["button.background"]
