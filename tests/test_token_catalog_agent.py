"""Tests for token_catalog.run_token_catalog."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from daf.agents.token_catalog import run_token_catalog

SEMANTIC_TOKENS = {
    "color.interactive.default": "#005FCC",
    "space.4": "16px",
}


@pytest.fixture
def output_dir(tmp_path):
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "semantic.tokens.json").write_text(json.dumps(SEMANTIC_TOKENS))
    (tmp_path / "docs" / "tokens").mkdir(parents=True)
    return str(tmp_path)


def test_creates_catalog_file(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "A color token used for interactive elements."
        run_token_catalog(output_dir)
    assert (tmp_path / "docs" / "tokens" / "catalog.md").exists()


def test_catalog_contains_token_path(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "Usage description."
        run_token_catalog(output_dir)
    content = (tmp_path / "docs" / "tokens" / "catalog.md").read_text()
    assert "color.interactive.default" in content


def test_catalog_contains_resolved_value(output_dir, tmp_path):
    with patch("daf.agents.token_catalog._call_llm") as mock_llm:
        mock_llm.return_value = "Usage description."
        run_token_catalog(output_dir)
    content = (tmp_path / "docs" / "tokens" / "catalog.md").read_text()
    assert "#005FCC" in content
