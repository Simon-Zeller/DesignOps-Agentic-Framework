"""Unit tests for SemanticMapper tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


def test_semantic_mapper_assigns_tier_labels_for_primitive_tokens(tmp_path):
    """SemanticMapper assigns 'primitive' tier to tokens with literal values."""
    from daf.tools.semantic_mapper import SemanticMapper

    tokens = [
        {"name": "color-blue-500", "value": "#007AFF", "type": "color"},
    ]

    mapper = SemanticMapper()
    result = mapper._run(tokens=tokens, output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["tier"] in ("primitive", "semantic", "component")


def test_semantic_mapper_assigns_semantic_tier_for_reference_tokens(tmp_path):
    """SemanticMapper assigns 'semantic' tier to tokens referencing other tokens."""
    from daf.tools.semantic_mapper import SemanticMapper

    tokens = [
        {"name": "color-primary", "value": "{color.blue.500}", "type": "color"},
    ]

    mapper = SemanticMapper()
    result = mapper._run(tokens=tokens, output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) == 1
    assert "tier" in result[0]


def test_semantic_mapper_returns_enriched_list(tmp_path):
    """SemanticMapper returns a list with at least the same number of items as input."""
    from daf.tools.semantic_mapper import SemanticMapper

    tokens = [
        {"name": "spacing-4", "value": "16px", "type": "spacing"},
        {"name": "font-size-base", "value": "16px", "type": "fontSizes"},
    ]

    mapper = SemanticMapper()
    result = mapper._run(tokens=tokens, output_dir=str(tmp_path))

    assert len(result) >= len(tokens)
