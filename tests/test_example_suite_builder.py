"""Tests for ExampleSuiteBuilder tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path


def test_writes_codemod_files_to_docs_codemods(tmp_path: Path) -> None:
    """Writes at least one .md file inside docs/codemods/."""
    codemods_dir = tmp_path / "docs" / "codemods"
    codemods_dir.mkdir(parents=True)

    from daf.tools.example_suite_builder import ExampleSuiteBuilder

    builder = ExampleSuiteBuilder(output_dir=str(tmp_path))
    codemods = [
        {"element": "button", "ds_component": "Button", "content": "# Codemod\n```\nbefore\n```"}
    ]
    builder._run(json.dumps(codemods))
    md_files = list(codemods_dir.glob("*.md"))
    assert len(md_files) >= 1


def test_writes_readme_when_no_targets_exist(tmp_path: Path) -> None:
    """Writes docs/codemods/README.md when the targets list is empty."""
    codemods_dir = tmp_path / "docs" / "codemods"
    codemods_dir.mkdir(parents=True)

    from daf.tools.example_suite_builder import ExampleSuiteBuilder

    builder = ExampleSuiteBuilder(output_dir=str(tmp_path))
    builder._run(json.dumps([]))
    readme = codemods_dir / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "no migration" in content.lower() or "no codemod" in content.lower()
