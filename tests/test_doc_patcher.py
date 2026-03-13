"""Tests for daf.tools.doc_patcher — patch_docs and DocPatcher tool."""
from __future__ import annotations

from pathlib import Path

from daf.tools.doc_patcher import DocPatcher, patch_docs


def _make_docs(tmp_path: Path, component: str, content: str) -> Path:
    docs_dir = tmp_path / "docs" / "components"
    docs_dir.mkdir(parents=True)
    md = docs_dir / f"{component.lower()}.md"
    md.write_text(content, encoding="utf-8")
    return md


def test_patch_docs_appends_missing_prop(tmp_path: Path) -> None:
    """Missing prop row is appended to the markdown file."""
    md = _make_docs(tmp_path, "Button", "# Button\n| Prop | Type | Default |\n|------|------|---------|")
    fixable = [{"component": "Button", "prop": "disabled", "category": "auto-fixable"}]
    result = patch_docs(str(tmp_path), fixable)
    assert len(result["patched"]) == 1
    assert result["patched"][0]["prop"] == "disabled"
    assert "disabled" in md.read_text()


def test_patch_docs_skips_missing_md(tmp_path: Path) -> None:
    """Component with no markdown file is silently skipped."""
    (tmp_path / "docs" / "components").mkdir(parents=True)
    fixable = [{"component": "Ghost", "prop": "size", "category": "auto-fixable"}]
    result = patch_docs(str(tmp_path), fixable)
    assert result["patched"] == []


def test_patch_docs_skips_existing_prop(tmp_path: Path) -> None:
    """Prop already in markdown content is not duplicated."""
    _make_docs(tmp_path, "Input", "# Input\n| disabled | bool | false |")
    fixable = [{"component": "Input", "prop": "disabled", "category": "auto-fixable"}]
    result = patch_docs(str(tmp_path), fixable)
    assert result["patched"] == []


def test_patch_docs_empty_fixable(tmp_path: Path) -> None:
    """Empty fixable list returns empty patched list."""
    result = patch_docs(str(tmp_path), [])
    assert result == {"patched": []}


def test_patch_docs_no_docs_dir(tmp_path: Path) -> None:
    """No docs/components directory → empty patched list."""
    fixable = [{"component": "X", "prop": "y", "category": "auto-fixable"}]
    result = patch_docs(str(tmp_path), fixable)
    assert result["patched"] == []


def test_doc_patcher_tool_type() -> None:
    """DocPatcher is a BaseTool."""
    from crewai.tools import BaseTool
    assert isinstance(DocPatcher(), BaseTool)


def test_doc_patcher_tool_run(tmp_path: Path) -> None:
    """DocPatcher._run delegates to patch_docs."""
    _make_docs(tmp_path, "Card", "# Card\n| Prop | Type |\n|------|------|")
    tool = DocPatcher()
    fixable = [{"component": "Card", "prop": "elevated", "category": "auto-fixable"}]
    result = tool._run(output_dir=str(tmp_path), fixable_items=fixable)
    assert len(result["patched"]) == 1
    assert result["patched"][0]["prop"] == "elevated"
