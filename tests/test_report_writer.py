"""Unit tests for report_writer — full run, partial failure, all-fail, directory creation."""
from __future__ import annotations

import json
from pathlib import Path


def _make_result(name: str, success: bool) -> dict:
    return {
        "component": name,
        "files_written": [f"src/components/{name}/{name}.tsx"] if success else [],
        "confidence": 90 if success else 0,
        "warnings": [],
    }


def test_writes_valid_json_for_full_success(tmp_path):
    """10 successful components → generation-summary.json with generated=10, failed=0."""
    from daf.tools.report_writer import write_generation_summary

    results = [_make_result(f"Comp{i}", True) for i in range(10)]
    write_generation_summary(results, str(tmp_path))

    report_path = tmp_path / "reports" / "generation-summary.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["total_components"] == 10
    assert data["generated"] == 10
    assert data["failed"] == 0


def test_partial_failure_correctly_reflected(tmp_path):
    """9 successes + 1 failure → generated=9, failed=1."""
    from daf.tools.report_writer import write_generation_summary

    results = [_make_result(f"Comp{i}", True) for i in range(9)]
    results.append(_make_result("BadComp", False))
    write_generation_summary(results, str(tmp_path))

    data = json.loads((tmp_path / "reports" / "generation-summary.json").read_text())
    assert data["generated"] == 9
    assert data["failed"] == 1


def test_report_written_even_when_all_fail(tmp_path):
    """All 3 components failing → valid JSON with failed=3."""
    from daf.tools.report_writer import write_generation_summary

    results = [_make_result(f"Comp{i}", False) for i in range(3)]
    write_generation_summary(results, str(tmp_path))

    report_path = tmp_path / "reports" / "generation-summary.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["failed"] == 3


def test_directory_is_created_if_absent(tmp_path):
    """write_generation_summary creates the reports/ dir if it doesn't exist."""
    from daf.tools.report_writer import write_generation_summary

    # Don't pre-create reports dir
    output_dir = tmp_path / "new_output"
    output_dir.mkdir()

    results = [_make_result("Box", True)]
    write_generation_summary(results, str(output_dir))

    assert (output_dir / "reports" / "generation-summary.json").exists()


# ---------------------------------------------------------------------------
# ReportWriter BaseTool — governance/quality-gates.json
# ---------------------------------------------------------------------------

def test_report_writer_tool_writes_file(tmp_path):
    """ReportWriter._run writes gate results to the given output_path."""
    from daf.tools.report_writer import ReportWriter

    writer = ReportWriter()
    gate_results = {
        "Button": {
            "coverage_80": True,
            "a11y_zero_critical": True,
            "no_phantom_refs": True,
            "has_docs": True,
            "has_usage_example": True,
        },
        "Input": {
            "coverage_80": False,
            "a11y_zero_critical": True,
            "no_phantom_refs": True,
            "has_docs": True,
            "has_usage_example": False,
        },
    }
    out_file = tmp_path / "governance" / "quality-gates.json"
    writer._run(results=gate_results, output_path=str(out_file))

    assert out_file.exists()


def test_report_writer_tool_valid_json(tmp_path):
    """ReportWriter._run writes valid JSON that can be parsed."""
    from daf.tools.report_writer import ReportWriter

    writer = ReportWriter()
    gate_results = {"Card": {"coverage_80": True, "a11y_zero_critical": False}}
    out_file = tmp_path / "quality-gates.json"
    writer._run(results=gate_results, output_path=str(out_file))

    data = json.loads(out_file.read_text())
    assert "Card" in data


def test_report_writer_tool_contains_component_names(tmp_path):
    """ReportWriter._run output JSON contains expected component names."""
    from daf.tools.report_writer import ReportWriter

    writer = ReportWriter()
    gate_results = {
        "Alert": {"coverage_80": True},
        "Badge": {"coverage_80": False},
    }
    out_file = tmp_path / "quality-gates.json"
    writer._run(results=gate_results, output_path=str(out_file))

    data = json.loads(out_file.read_text())
    assert "Alert" in data
    assert "Badge" in data
