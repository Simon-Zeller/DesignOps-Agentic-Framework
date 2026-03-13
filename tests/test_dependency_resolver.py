"""Tests for DependencyResolver tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


def test_returns_npm_unavailable_when_npm_not_on_path(tmp_path: Path) -> None:
    """Returns {'status': 'npm_unavailable'} when npm is not found."""
    from daf.tools.dependency_resolver import DependencyResolver

    resolver = DependencyResolver(output_dir=str(tmp_path))
    with patch("subprocess.run", side_effect=FileNotFoundError("npm not found")):
        result = resolver._run("npm install")
    assert result["status"] == "npm_unavailable"


def test_returns_success_when_command_exits_0(tmp_path: Path) -> None:
    """Returns {'status': 'success', 'stdout': ...} on exit code 0."""
    from daf.tools.dependency_resolver import DependencyResolver

    resolver = DependencyResolver(output_dir=str(tmp_path))
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "installed"
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        result = resolver._run("npm install")
    assert result["status"] == "success"
    assert result["stdout"] == "installed"


def test_returns_failed_dict_when_command_exits_non_zero(tmp_path: Path) -> None:
    """Returns {'status': 'failed', 'exit_code': N, 'stderr': ...} on non-zero exit."""
    from daf.tools.dependency_resolver import DependencyResolver

    resolver = DependencyResolver(output_dir=str(tmp_path))
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error: cannot find module"
    with patch("subprocess.run", return_value=mock_result):
        result = resolver._run("npm install")
    assert result["status"] == "failed"
    assert result["exit_code"] == 1
    assert result["stderr"] == "error: cannot find module"


def test_never_raises_unhandled_exception(tmp_path: Path) -> None:
    """No exception propagates on arbitrary OSError."""
    from daf.tools.dependency_resolver import DependencyResolver

    resolver = DependencyResolver(output_dir=str(tmp_path))
    with patch("subprocess.run", side_effect=OSError("broken pipe")):
        result = resolver._run("npm install")
    assert result["status"] == "npm_unavailable"
