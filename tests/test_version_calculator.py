"""Tests for VersionCalculator tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path


def test_returns_v1_0_0_when_all_fatal_gates_pass(tmp_path: Path) -> None:
    """Returns 'v1.0.0' when fatal_failed == 0."""
    from daf.tools.version_calculator import VersionCalculator

    calc = VersionCalculator(output_dir=str(tmp_path))
    result = calc._run('{"fatal_failed": 0, "fatal_passed": 8}')
    assert result == "v1.0.0"


def test_returns_v0_x_0_when_any_fatal_gate_fails(tmp_path: Path) -> None:
    """Returns version starting with 'v0.' when fatal_failed > 0."""
    from daf.tools.version_calculator import VersionCalculator

    calc = VersionCalculator(output_dir=str(tmp_path))
    result = calc._run('{"fatal_failed": 2, "fatal_passed": 6}')
    assert result.startswith("v0.")


def test_returns_experimental_on_malformed_input(tmp_path: Path) -> None:
    """Returns 'v0.1.0-experimental' on malformed input."""
    from daf.tools.version_calculator import VersionCalculator

    calc = VersionCalculator(output_dir=str(tmp_path))
    result = calc._run("not valid json {{")
    assert result == "v0.1.0-experimental"
