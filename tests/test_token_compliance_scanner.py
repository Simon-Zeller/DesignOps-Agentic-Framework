"""Tests for daf.tools.token_compliance_scanner — scan_compliance and TokenComplianceScannerTool."""
from __future__ import annotations

from pathlib import Path

from daf.tools.token_compliance_scanner import TokenComplianceScannerTool, scan_compliance


def test_scan_compliance_no_src_dir(tmp_path: Path) -> None:
    """Missing src/ directory → empty files list, compliance_score 1.0."""
    result = scan_compliance(str(tmp_path))
    assert result["files"] == []
    assert result["summary"]["total_violations"] == 0
    assert result["summary"]["compliance_score"] == 1.0


def test_scan_compliance_empty_src(tmp_path: Path) -> None:
    """Empty src/ directory (no TSX files) → empty files list."""
    (tmp_path / "src").mkdir()
    result = scan_compliance(str(tmp_path))
    assert result["files"] == []
    assert result["summary"]["compliance_score"] == 1.0


def test_scan_compliance_with_tsx_violations(tmp_path: Path) -> None:
    """TSX file with hardcoded hex → reported in files list with violations."""
    src = tmp_path / "src"
    src.mkdir()
    tsx = src / "Button.tsx"
    tsx.write_text("const style = { color: '#ff0000' };", encoding="utf-8")

    result = scan_compliance(str(tmp_path))
    assert len(result["files"]) == 1
    assert result["files"][0]["hardcoded_values"] >= 1
    assert result["summary"]["total_violations"] >= 1
    assert result["summary"]["compliance_score"] < 1.0


def test_scan_compliance_with_clean_tsx(tmp_path: Path) -> None:
    """TSX file using only var(--token) → zero violations."""
    src = tmp_path / "src"
    src.mkdir()
    tsx = src / "Clean.tsx"
    tsx.write_text("const style = { color: 'var(--color-primary)' };", encoding="utf-8")

    result = scan_compliance(str(tmp_path))
    assert len(result["files"]) == 1
    assert result["files"][0]["hardcoded_values"] == 0
    assert result["summary"]["total_violations"] == 0


def test_token_compliance_scanner_tool_type() -> None:
    """TokenComplianceScannerTool is a BaseTool."""
    from crewai.tools import BaseTool
    assert isinstance(TokenComplianceScannerTool(), BaseTool)


def test_token_compliance_scanner_tool_run(tmp_path: Path) -> None:
    """TokenComplianceScannerTool._run delegates to scan_compliance."""
    (tmp_path / "src").mkdir()
    tool = TokenComplianceScannerTool()
    result = tool._run(output_dir=str(tmp_path))
    assert "files" in result
    assert "summary" in result
    assert result["summary"]["compliance_score"] == 1.0
