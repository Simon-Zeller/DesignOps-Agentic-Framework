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
