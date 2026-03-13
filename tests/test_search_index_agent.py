"""Tests for search_index.run_search_index."""
import json
from pathlib import Path

import pytest

from daf.agents.search_index import run_search_index


@pytest.fixture
def output_dir(tmp_path):
    docs = tmp_path / "docs"
    (docs / "components").mkdir(parents=True)
    (docs / "tokens").mkdir(parents=True)
    (docs / "decisions").mkdir(parents=True)
    (docs / "components" / "Button.md").write_text(
        "# Button\n\nA pressable component with label prop.\n"
    )
    (docs / "tokens" / "catalog.md").write_text(
        "# Token Catalog\n\n## color.interactive.default\n\nValue: #005FCC\n"
    )
    (docs / "decisions" / "adr-archetype-selection.md").write_text(
        "# ADR: Archetype Selection\n\n## Context\nMinimalist brand.\n"
    )
    (docs / "README.md").write_text("# Design System\n\nInstall via npm.\n")
    return str(tmp_path)


def test_creates_search_index_file(output_dir, tmp_path):
    run_search_index(output_dir)
    assert (tmp_path / "docs" / "search-index.json").exists()


def test_search_index_is_valid_json(output_dir, tmp_path):
    run_search_index(output_dir)
    content = (tmp_path / "docs" / "search-index.json").read_text()
    data = json.loads(content)
    assert isinstance(data, list)


def test_search_index_contains_component_entries(output_dir, tmp_path):
    run_search_index(output_dir)
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    categories = [e.get("category") for e in data]
    assert "component" in categories


def test_search_index_contains_token_entries(output_dir, tmp_path):
    run_search_index(output_dir)
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    categories = [e.get("category") for e in data]
    assert "token" in categories


def test_empty_docs_produces_empty_index(tmp_path):
    (tmp_path / "docs").mkdir()
    run_search_index(str(tmp_path))
    data = json.loads((tmp_path / "docs" / "search-index.json").read_text())
    assert data == []
