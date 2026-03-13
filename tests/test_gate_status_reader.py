"""Tests for GateStatusReader tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_returns_pass_fail_counts_from_valid_json(tmp_path: Path) -> None:
    """Returns structured pass/fail counts from valid quality-gates.json."""
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    gates = [
        {"name": f"gate_{i}", "severity": "fatal", "passed": True}
        for i in range(8)
    ]
    (gate_dir / "quality-gates.json").write_text(json.dumps({"gates": gates}))

    from daf.tools.gate_status_reader import GateStatusReader

    reader = GateStatusReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert isinstance(result, dict)
    assert result["fatal_passed"] == 8
    assert result["fatal_failed"] == 0


def test_returns_safe_default_when_file_absent(tmp_path: Path) -> None:
    """Returns zero-counts default when quality-gates.json does not exist."""
    from daf.tools.gate_status_reader import GateStatusReader

    reader = GateStatusReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert result["fatal_passed"] == 0
    assert result["fatal_failed"] == 0
    assert result["gates"] == []


def test_returns_warning_on_fallback(tmp_path: Path) -> None:
    """Result includes warnings key when falling back to default (file absent)."""
    from daf.tools.gate_status_reader import GateStatusReader

    reader = GateStatusReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert "warnings" in result
    assert len(result["warnings"]) > 0
