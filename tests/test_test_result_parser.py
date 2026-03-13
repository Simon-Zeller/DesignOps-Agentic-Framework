"""Tests for TestResultParser tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path


def test_parses_passing_test_output(tmp_path: Path) -> None:
    """Parses Vitest success output into {'passed': 10, 'failed': 0, 'skipped': 0}."""
    from daf.tools.test_result_parser import TestResultParser

    parser = TestResultParser(output_dir=str(tmp_path))
    stdout = "Tests  10 passed (10)\nDuration  1.23s\n"
    result = parser._run(stdout)
    assert result["passed"] == 10
    assert result["failed"] == 0


def test_parses_failing_test_output(tmp_path: Path) -> None:
    """Parses Vitest output with failures into correct counts."""
    from daf.tools.test_result_parser import TestResultParser

    parser = TestResultParser(output_dir=str(tmp_path))
    stdout = "Tests  8 passed | 2 failed (10)\nDuration  2.11s\n"
    result = parser._run(stdout)
    assert result["passed"] == 8
    assert result["failed"] == 2


def test_handles_empty_stdout(tmp_path: Path) -> None:
    """Returns all-zero dict on empty input."""
    from daf.tools.test_result_parser import TestResultParser

    parser = TestResultParser(output_dir=str(tmp_path))
    result = parser._run("")
    assert result == {"passed": 0, "failed": 0, "skipped": 0}
