"""Unit tests for TokenUsageMapper tool."""
from __future__ import annotations

import json


def test_token_usage_mapper_detects_dead_token(tmp_path):
    """Token defined in tokens/ but not used in any TSX is reported as dead."""
    from daf.tools.token_usage_mapper import TokenUsageMapper

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    token_data = {
        "color-background-subtle": {"$type": "color", "$value": "#f5f5f5"}
    }
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps(token_data))

    # No TSX files at all
    result = TokenUsageMapper()._run(str(tmp_path))
    assert "color-background-subtle" in result["dead_tokens"]


def test_token_usage_mapper_no_dead_tokens_when_all_referenced(tmp_path):
    """No dead tokens when all defined tokens are referenced in TSX files."""
    from daf.tools.token_usage_mapper import TokenUsageMapper

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    token_data = {
        "color-text-primary": {"$type": "color", "$value": "#111111"}
    }
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps(token_data))

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Button.tsx").write_text("const s = { color: 'var(--color-text-primary)' };\n")

    result = TokenUsageMapper()._run(str(tmp_path))
    assert "color-text-primary" not in result["dead_tokens"]


def test_token_usage_mapper_returns_empty_when_no_tokens_dir(tmp_path):
    """Returns valid structure when no tokens/ directory exists."""
    from daf.tools.token_usage_mapper import TokenUsageMapper

    result = TokenUsageMapper()._run(str(tmp_path))
    assert "dead_tokens" in result
    assert "phantom_refs" in result
    assert "used_tokens" in result
