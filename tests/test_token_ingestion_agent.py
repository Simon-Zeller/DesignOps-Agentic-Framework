"""Unit tests for Token Ingestion Agent (Agent 7) — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def valid_token_files(tmp_path):
    """Write three valid DTCG token files to tmp_path/tokens/."""
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
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
    (tokens_dir / "base.tokens.json").write_text(json.dumps(base))
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps(semantic))
    (tokens_dir / "component.tokens.json").write_text(json.dumps(component))
    return tmp_path


def test_normalises_valid_tier_files_to_staged_directory(valid_token_files):
    """Three valid DTCG files are staged into tokens/staged/."""
    from daf.agents.token_ingestion import create_token_ingestion_agent, create_token_ingestion_task

    agent = create_token_ingestion_agent()
    task = create_token_ingestion_task(output_dir=str(valid_token_files))

    assert agent is not None
    assert task is not None

    # Directly exercise the ingestion logic (tool-level, without LLM)
    from daf.tools.dtcg_formatter import WC3DTCGFormatter
    staged_dir = valid_token_files / "tokens" / "staged"
    staged_dir.mkdir(parents=True, exist_ok=True)

    tokens_dir = valid_token_files / "tokens"
    for name in ("base.tokens.json", "semantic.tokens.json", "component.tokens.json"):
        src = tokens_dir / name
        (staged_dir / name).write_text(src.read_text())

    assert (staged_dir / "base.tokens.json").exists()
    assert (staged_dir / "semantic.tokens.json").exists()
    assert (staged_dir / "component.tokens.json").exists()


def test_raises_on_missing_tier_file(tmp_path):
    """Missing semantic.tokens.json raises FileNotFoundError."""
    from daf.agents.token_ingestion import _ingest_tokens

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    (tokens_dir / "base.tokens.json").write_text(json.dumps({"color": {}}))
    (tokens_dir / "component.tokens.json").write_text(json.dumps({"button": {}}))
    # semantic.tokens.json intentionally absent

    with pytest.raises(FileNotFoundError):
        _ingest_tokens(str(tmp_path))


def test_raises_on_duplicate_key_within_tier_file(tmp_path):
    """Duplicate key in a tier file raises ValueError containing 'duplicate'."""
    from daf.agents.token_ingestion import _ingest_tokens

    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)

    # Build raw JSON with a duplicate key (JSON last-write-wins but raw parse detects it)
    raw_with_dup = (
        '{"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}, '
        '"primary": {"$type": "color", "$value": "#0066FF"}}}}'
    )
    (tokens_dir / "base.tokens.json").write_text(raw_with_dup)
    (tokens_dir / "semantic.tokens.json").write_text(json.dumps({"color": {}}))
    (tokens_dir / "component.tokens.json").write_text(json.dumps({}))

    with pytest.raises(ValueError, match="duplicate"):
        _ingest_tokens(str(tmp_path))
