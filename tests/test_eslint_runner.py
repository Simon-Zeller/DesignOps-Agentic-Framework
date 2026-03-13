"""Unit tests for eslint_runner — structured violations and clean file."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_returns_structured_violations(tmp_path):
    """run_eslint returns a list of violation dicts with rule, message, and line fields."""
    from daf.tools.eslint_runner import run_eslint

    tsx_file = tmp_path / "Button.tsx"
    tsx_file.write_text("const style = { color: '#1a1a1a' };\n")

    eslint_output = json.dumps([
        {
            "filePath": str(tsx_file),
            "messages": [
                {"ruleId": "no-hardcoded-values", "message": "Hardcoded color value", "line": 1}
            ],
        }
    ])

    with patch("daf.tools.eslint_runner.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout=eslint_output, stderr="")
        violations = run_eslint(str(tsx_file))

    assert isinstance(violations, list)
    assert len(violations) == 1
    assert violations[0]["rule"] == "no-hardcoded-values"
    assert violations[0]["message"] == "Hardcoded color value"
    assert violations[0]["line"] == 1


def test_returns_empty_list_for_clean_file(tmp_path):
    """run_eslint returns [] for a file with no violations."""
    from daf.tools.eslint_runner import run_eslint

    tsx_file = tmp_path / "Clean.tsx"
    tsx_file.write_text("export const x = 1;\n")

    eslint_output = json.dumps([
        {"filePath": str(tsx_file), "messages": []}
    ])

    with patch("daf.tools.eslint_runner.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=eslint_output, stderr="")
        violations = run_eslint(str(tsx_file))

    assert violations == []
