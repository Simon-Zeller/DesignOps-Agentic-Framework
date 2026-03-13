"""Tests for coverage_reporter.py."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from daf.tools.coverage_reporter import get_coverage

LCOV_FIXTURE = {
    "Button.tsx": {
        "lines": {"total": 40, "covered": 38, "pct": 95.0},
        "functions": {"total": 2, "covered": 2, "pct": 100.0},
        "branches": {"total": 4, "covered": 3, "pct": 75.0},
        "statements": {"total": 40, "covered": 38, "pct": 95.0},
    }
}


@pytest.fixture
def coverage_file(tmp_path):
    p = tmp_path / "lcov.json"
    p.write_text(json.dumps(LCOV_FIXTURE))
    return str(p)


def test_returns_line_coverage_from_fixture(coverage_file):
    result = get_coverage("Button.tsx", coverage_file)
    assert result == pytest.approx(0.95)


def test_returns_none_when_file_absent():
    result = get_coverage("Button.tsx", "/nonexistent/path/lcov.json")
    assert result is None


def test_returns_none_for_missing_component(coverage_file):
    result = get_coverage("NewComponent.tsx", coverage_file)
    assert result is None
