"""Unit tests for TokenGraphTraverser tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_token_graph_traverser_resolves_semantic_token(tmp_path):
    """TokenGraphTraverser resolves a token with a $value to its resolved value."""
    from daf.tools.token_graph_traverser import TokenGraphTraverser

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    token_data = {
        "color": {
            "primary": {
                "$value": "#007AFF",
                "$type": "color",
            }
        }
    }
    (tokens_dir / "color.tokens.json").write_text(json.dumps(token_data))

    traverser = TokenGraphTraverser()
    result = traverser._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) >= 1
    token = result[0]
    assert "name" in token
    assert "value" in token
    assert token["value"] == "#007AFF"


def test_token_graph_traverser_handles_empty_token_file(tmp_path):
    """TokenGraphTraverser handles an empty token file gracefully."""
    from daf.tools.token_graph_traverser import TokenGraphTraverser

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "empty.tokens.json").write_text("{}")

    traverser = TokenGraphTraverser()
    result = traverser._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert result == []


def test_token_graph_traverser_handles_missing_tokens_directory(tmp_path):
    """TokenGraphTraverser returns empty list when tokens/ directory does not exist."""
    from daf.tools.token_graph_traverser import TokenGraphTraverser

    traverser = TokenGraphTraverser()
    result = traverser._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert result == []
