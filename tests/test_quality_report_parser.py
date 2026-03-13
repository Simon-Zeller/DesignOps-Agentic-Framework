"""Tests for QualityReportParser tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path


def test_parses_gate_json_into_structured_summary(tmp_path: Path) -> None:
    """Parses quality-gates.json into passed_gates, failed_gates, warnings."""
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    gates = [
        {"name": "token_validity", "severity": "fatal", "passed": True},
        {"name": "wcag_contrast", "severity": "fatal", "passed": False},
        {"name": "coverage_80", "severity": "warning", "passed": False},
    ]
    (gate_dir / "quality-gates.json").write_text(json.dumps({"gates": gates}))

    from daf.tools.quality_report_parser import QualityReportParser

    parser = QualityReportParser(output_dir=str(tmp_path))
    result = parser._run("")
    assert "passed_gates" in result
    assert "failed_gates" in result
    assert "warnings" in result
    assert "token_validity" in result["passed_gates"]
    assert "wcag_contrast" in result["failed_gates"]
    assert "coverage_80" in result["warnings"]


def test_handles_missing_report_gracefully(tmp_path: Path) -> None:
    """Returns empty structure when quality-gates.json does not exist."""
    from daf.tools.quality_report_parser import QualityReportParser

    parser = QualityReportParser(output_dir=str(tmp_path))
    result = parser._run("")
    assert result["passed_gates"] == []
    assert result["failed_gates"] == []
    assert result["warnings"] == []
