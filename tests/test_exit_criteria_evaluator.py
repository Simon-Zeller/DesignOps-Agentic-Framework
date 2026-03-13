"""Tests for ExitCriteriaEvaluator tool (p19-exit-criteria, TDD red phase)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def _make_evaluator(output_dir: str):
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    return ExitCriteriaEvaluator()


def _mock_all_checks_pass(mock_target: str = "daf.tools.exit_criteria_evaluator"):
    """Return a context manager that patches all 15 _check_cN methods to pass=True."""
    from daf.tools.exit_criteria_evaluator import CriterionResult
    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    WARN_IDS = {9, 10, 11, 12, 13, 14, 15}

    patches = []
    for i in range(1, 16):
        sev = "fatal" if i in FATAL_IDS else "warning"
        result = CriterionResult(
            id=i,
            description=f"C{i} criterion",
            severity=sev,
            passed=True,
            detail="",
        )
        p = patch(f"{mock_target}.ExitCriteriaEvaluator._check_c{i}", return_value=result)
        patches.append(p)
    return patches


# ---------------------------------------------------------------------------
# 1.1 test_evaluator_returns_15_criteria_items
# ---------------------------------------------------------------------------

def test_evaluator_returns_15_criteria_items(tmp_path: Path) -> None:
    """ExitCriteriaEvaluator._run returns a result with exactly 15 criteria items."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    with patch.multiple(
        ExitCriteriaEvaluator,
        **{
            f"_check_c{i}": MagicMock(return_value=CriterionResult(
                id=i,
                description=f"C{i}",
                severity="fatal" if i in FATAL_IDS else "warning",
                passed=True,
                detail="",
            ))
            for i in range(1, 16)
        }
    ):
        result = evaluator._run(output_dir=str(tmp_path))

    assert len(result["criteria"]) == 15


# ---------------------------------------------------------------------------
# 1.2 test_is_complete_true_when_all_fatal_pass
# ---------------------------------------------------------------------------

def test_is_complete_true_when_all_fatal_pass(tmp_path: Path) -> None:
    """isComplete is True when all Fatal criteria (C1–C8) pass."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    with patch.multiple(
        ExitCriteriaEvaluator,
        **{
            f"_check_c{i}": MagicMock(return_value=CriterionResult(
                id=i,
                description=f"C{i}",
                severity="fatal" if i in FATAL_IDS else "warning",
                passed=True,
                detail="",
            ))
            for i in range(1, 16)
        }
    ):
        result = evaluator._run(output_dir=str(tmp_path))

    assert result["isComplete"] is True


# ---------------------------------------------------------------------------
# 1.3 test_is_complete_false_when_one_fatal_fails
# ---------------------------------------------------------------------------

def test_is_complete_false_when_one_fatal_fails(tmp_path: Path) -> None:
    """isComplete is False when at least one Fatal criterion (C1) fails."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    mocks = {
        f"_check_c{i}": MagicMock(return_value=CriterionResult(
            id=i,
            description=f"C{i}",
            severity="fatal" if i in FATAL_IDS else "warning",
            passed=(i != 1),  # C1 fails
            detail="fails" if i == 1 else "",
        ))
        for i in range(1, 16)
    }
    with patch.multiple(ExitCriteriaEvaluator, **mocks):
        result = evaluator._run(output_dir=str(tmp_path))

    assert result["isComplete"] is False


# ---------------------------------------------------------------------------
# 1.4 test_is_complete_true_when_only_warnings_fail
# ---------------------------------------------------------------------------

def test_is_complete_true_when_only_warnings_fail(tmp_path: Path) -> None:
    """isComplete is True when only Warning criteria fail (C9)."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    mocks = {
        f"_check_c{i}": MagicMock(return_value=CriterionResult(
            id=i,
            description=f"C{i}",
            severity="fatal" if i in FATAL_IDS else "warning",
            passed=(i != 9),  # C9 (warning) fails, all fatal pass
            detail="fails" if i == 9 else "",
        ))
        for i in range(1, 16)
    }
    with patch.multiple(ExitCriteriaEvaluator, **mocks):
        result = evaluator._run(output_dir=str(tmp_path))

    assert result["isComplete"] is True


# ---------------------------------------------------------------------------
# 1.5 test_evaluator_writes_exit_criteria_json
# ---------------------------------------------------------------------------

def test_evaluator_writes_exit_criteria_json(tmp_path: Path) -> None:
    """ExitCriteriaEvaluator._run writes reports/exit-criteria.json to disk."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    with patch.multiple(
        ExitCriteriaEvaluator,
        **{
            f"_check_c{i}": MagicMock(return_value=CriterionResult(
                id=i, description=f"C{i}",
                severity="fatal" if i in FATAL_IDS else "warning",
                passed=True, detail="",
            ))
            for i in range(1, 16)
        }
    ):
        evaluator._run(output_dir=str(tmp_path))

    report_path = tmp_path / "reports" / "exit-criteria.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert "isComplete" in data


# ---------------------------------------------------------------------------
# 1.6 test_evaluator_continues_after_file_not_found
# ---------------------------------------------------------------------------

def test_evaluator_continues_after_file_not_found(tmp_path: Path) -> None:
    """Evaluator continues when C1 raises FileNotFoundError; C1 is marked failed."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}

    def _c1_raises(*args, **kwargs):
        raise FileNotFoundError("tokens/ not found")

    mocks: dict = {
        "_check_c1": MagicMock(side_effect=_c1_raises),
    }
    mocks.update({
        f"_check_c{i}": MagicMock(return_value=CriterionResult(
            id=i, description=f"C{i}",
            severity="fatal" if i in FATAL_IDS else "warning",
            passed=True, detail="",
        ))
        for i in range(2, 16)
    })
    with patch.multiple(ExitCriteriaEvaluator, **mocks):
        result = evaluator._run(output_dir=str(tmp_path))

    assert len(result["criteria"]) == 15
    c1 = next(c for c in result["criteria"] if c["id"] == 1)
    assert c1["passed"] is False
    assert c1["detail"]
    assert result["isComplete"] is False


# ---------------------------------------------------------------------------
# 1.7 test_all_criteria_have_sequential_ids
# ---------------------------------------------------------------------------

def test_all_criteria_have_sequential_ids(tmp_path: Path) -> None:
    """All criteria have sequential IDs 1–15 in the result."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator, CriterionResult
    evaluator = ExitCriteriaEvaluator()

    FATAL_IDS = {1, 2, 3, 4, 5, 6, 7, 8}
    with patch.multiple(
        ExitCriteriaEvaluator,
        **{
            f"_check_c{i}": MagicMock(return_value=CriterionResult(
                id=i, description=f"C{i}",
                severity="fatal" if i in FATAL_IDS else "warning",
                passed=True, detail="",
            ))
            for i in range(1, 16)
        }
    ):
        result = evaluator._run(output_dir=str(tmp_path))

    ids = [c["id"] for c in result["criteria"]]
    assert ids == list(range(1, 16))


# ---------------------------------------------------------------------------
# C1 tests
# ---------------------------------------------------------------------------

def test_c1_passes_with_valid_token_files(tmp_path: Path) -> None:
    """_check_c1 passes when tokens/*.tokens.json contains valid JSON."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "global.tokens.json").write_text(json.dumps({"color": {"$value": "#fff", "$type": "color"}}))

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c1(str(tmp_path))

    assert result.passed is True
    assert result.id == 1
    assert result.severity == "fatal"


def test_c1_fails_with_invalid_json(tmp_path: Path) -> None:
    """_check_c1 fails when a token file contains invalid JSON."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "broken.tokens.json").write_text("{invalid")

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c1(str(tmp_path))

    assert result.passed is False
    assert "broken.tokens.json" in result.detail


def test_c1_fails_when_tokens_dir_absent(tmp_path: Path) -> None:
    """_check_c1 fails when tokens/ directory is not present."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c1(str(tmp_path))

    assert result.passed is False
    assert "tokens/ directory not found" in result.detail


# ---------------------------------------------------------------------------
# C2 tests
# ---------------------------------------------------------------------------

def test_c2_passes_when_dtcg_returns_empty_fatal(tmp_path: Path) -> None:
    """_check_c2 passes when DTCGSchemaValidator returns empty fatal list."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.DTCGSchemaValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance._run.return_value = {"fatal": [], "warnings": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c2(str(tmp_path))

    assert result.passed is True
    assert result.id == 2
    assert result.severity == "fatal"


def test_c2_fails_when_dtcg_returns_fatal_errors(tmp_path: Path) -> None:
    """_check_c2 fails when DTCGSchemaValidator returns non-empty fatal list."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.DTCGSchemaValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance._run.return_value = {"fatal": [{"token_path": "color.x", "detail": "missing $type", "check": "type"}], "warnings": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c2(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# C3 & C4 tests
# ---------------------------------------------------------------------------

def test_c3_passes_when_no_unresolved_refs(tmp_path: Path) -> None:
    """_check_c3 passes when TokenGraphTraverser returns no unresolved refs."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.TokenGraphTraverser") as MockTraverser:
        mock_instance = MockTraverser.return_value
        mock_instance._run.return_value = {"tokens": [], "unresolved_refs": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c3(str(tmp_path))

    assert result.passed is True
    assert result.id == 3
    assert result.severity == "fatal"


def test_c3_fails_with_unresolved_refs(tmp_path: Path) -> None:
    """_check_c3 fails when TokenGraphTraverser returns unresolved refs."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.TokenGraphTraverser") as MockTraverser:
        mock_instance = MockTraverser.return_value
        mock_instance._run.return_value = {"tokens": [], "unresolved_refs": ["color.brand.missing"]}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c3(str(tmp_path))

    assert result.passed is False
    assert "color.brand.missing" in result.detail


def test_c4_fails_with_component_unresolved_refs(tmp_path: Path) -> None:
    """_check_c4 fails when component-layer traversal returns unresolved refs."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.TokenGraphTraverser") as MockTraverser:
        mock_instance = MockTraverser.return_value
        mock_instance._run.return_value = {"tokens": [], "unresolved_refs": ["component.button.background"]}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c4(str(tmp_path))

    assert result.passed is False
    assert result.id == 4
    assert result.severity == "fatal"


# ---------------------------------------------------------------------------
# C5 tests
# ---------------------------------------------------------------------------

def test_c5_passes_when_contrast_all_pass_true(tmp_path: Path) -> None:
    """_check_c5 passes when ContrastSafePairer returns all_pass=True."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.ContrastSafePairer") as MockPairer:
        mock_instance = MockPairer.return_value
        mock_instance._run.return_value = {"all_pass": True, "pairs": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c5(str(tmp_path))

    assert result.passed is True
    assert result.id == 5
    assert result.severity == "fatal"


def test_c5_fails_when_contrast_all_pass_false(tmp_path: Path) -> None:
    """_check_c5 fails when ContrastSafePairer returns all_pass=False."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.ContrastSafePairer") as MockPairer:
        mock_instance = MockPairer.return_value
        mock_instance._run.return_value = {
            "all_pass": False,
            "pairs": [{"fg": "#fff", "bg": "#eee", "ratio": 1.2, "pass": False}],
        }
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c5(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# C6 tests
# ---------------------------------------------------------------------------

def test_c6_passes_when_all_refs_resolve(tmp_path: Path) -> None:
    """_check_c6 passes when check_token_refs returns all_resolved=True."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.check_token_refs") as mock_fn:
        mock_fn.return_value = {"all_resolved": True, "unresolved": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c6(str(tmp_path))

    assert result.passed is True
    assert result.id == 6
    assert result.severity == "fatal"


def test_c6_fails_with_unresolved_css_refs(tmp_path: Path) -> None:
    """_check_c6 fails when check_token_refs returns unresolved CSS refs."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.check_token_refs") as mock_fn:
        mock_fn.return_value = {"all_resolved": False, "unresolved": ["--color-brand-primary"]}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c6(str(tmp_path))

    assert result.passed is False
    assert "--color-brand-primary" in result.detail


# ---------------------------------------------------------------------------
# C7 tests
# ---------------------------------------------------------------------------

def test_c7_passes_when_tsc_exits_0(tmp_path: Path) -> None:
    """_check_c7 passes when tsc exits with code 0."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("daf.tools.exit_criteria_evaluator.subprocess.run", return_value=mock_result):
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c7(str(tmp_path))

    assert result.passed is True
    assert result.id == 7
    assert result.severity == "fatal"


def test_c7_fails_when_tsc_exits_nonzero(tmp_path: Path) -> None:
    """_check_c7 fails when tsc exits with non-zero code."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stderr = "error TS1234: some type error"

    with patch("daf.tools.exit_criteria_evaluator.subprocess.run", return_value=mock_result):
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c7(str(tmp_path))

    assert result.passed is False
    assert "TS1234" in result.detail


def test_c7_fails_gracefully_when_tsc_not_found(tmp_path: Path) -> None:
    """_check_c7 returns passed=False with 'tsc not found' when tsc is not installed."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.subprocess.run", side_effect=FileNotFoundError):
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c7(str(tmp_path))

    assert result.passed is False
    assert "tsc not found" in result.detail


def test_c7_fails_gracefully_on_timeout(tmp_path: Path) -> None:
    """_check_c7 returns passed=False when tsc times out."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch(
        "daf.tools.exit_criteria_evaluator.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="tsc", timeout=30),
    ):
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c7(str(tmp_path))

    assert result.passed is False
    assert "timed out" in result.detail


# ---------------------------------------------------------------------------
# C8 tests
# ---------------------------------------------------------------------------

def test_c8_passes_when_dep_resolver_succeeds(tmp_path: Path) -> None:
    """_check_c8 passes when DependencyResolver returns success."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.DependencyResolver") as MockResolver:
        mock_instance = MockResolver.return_value
        mock_instance._run.return_value = {"status": "success", "stdout": ""}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c8(str(tmp_path))

    assert result.passed is True
    assert result.id == 8
    assert result.severity == "fatal"


def test_c8_fails_when_dep_resolver_fails(tmp_path: Path) -> None:
    """_check_c8 fails when DependencyResolver returns failed status."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.DependencyResolver") as MockResolver:
        mock_instance = MockResolver.return_value
        mock_instance._run.return_value = {"status": "failed", "stderr": "npm ERR! missing peer dep", "exit_code": 1}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c8(str(tmp_path))

    assert result.passed is False
    assert "npm ERR" in result.detail


# ---------------------------------------------------------------------------
# C9 tests
# ---------------------------------------------------------------------------

def test_c9_passes_when_all_pass_true_in_summary(tmp_path: Path) -> None:
    """_check_c9 passes when generation-summary.json has test_results.all_pass=true."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "generation-summary.json").write_text(
        json.dumps({"test_results": {"all_pass": True}})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c9(str(tmp_path))

    assert result.passed is True
    assert result.id == 9
    assert result.severity == "warning"


def test_c9_fails_when_summary_absent(tmp_path: Path) -> None:
    """_check_c9 fails when generation-summary.json is not found."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c9(str(tmp_path))

    assert result.passed is False
    assert result.id == 9
    assert result.severity == "warning"


# ---------------------------------------------------------------------------
# C10 tests
# ---------------------------------------------------------------------------

def test_c10_passes_when_no_hardcoded_colors(tmp_path: Path) -> None:
    """_check_c10 passes when AstPatternMatcher returns no targets."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.ASTPatternMatcher") as MockMatcher:
        mock_instance = MockMatcher.return_value
        mock_instance._run.return_value = {"targets": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c10(str(tmp_path))

    assert result.passed is True
    assert result.id == 10
    assert result.severity == "warning"


def test_c10_fails_with_hardcoded_color_targets(tmp_path: Path) -> None:
    """_check_c10 fails when AstPatternMatcher returns hardcoded_color targets."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch("daf.tools.exit_criteria_evaluator.ASTPatternMatcher") as MockMatcher:
        mock_instance = MockMatcher.return_value
        mock_instance._run.return_value = {
            "targets": [{"type": "hardcoded_color", "pattern": "#333", "file": "Button.tsx", "line": 12}]
        }
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c10(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# C12 tests
# ---------------------------------------------------------------------------

def test_c12_passes_when_all_scores_above_70(tmp_path: Path) -> None:
    """_check_c12 passes when all quality gate scores are >= 70."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    (gate_dir / "quality-gates.json").write_text(
        json.dumps({"components": [{"name": "Button", "score": 85}, {"name": "Input", "score": 90}]})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c12(str(tmp_path))

    assert result.passed is True
    assert result.id == 12
    assert result.severity == "warning"


def test_c12_fails_when_any_score_below_70(tmp_path: Path) -> None:
    """_check_c12 fails when any component score is below 70."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    (gate_dir / "quality-gates.json").write_text(
        json.dumps({"components": [{"name": "Button", "score": 60}]})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c12(str(tmp_path))

    assert result.passed is False


def test_c12_fails_when_quality_gates_absent(tmp_path: Path) -> None:
    """_check_c12 fails when quality-gates.json is not found."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c12(str(tmp_path))

    assert result.passed is False


def test_c12_handles_malformed_components_field(tmp_path: Path) -> None:
    """_check_c12 fails gracefully when 'components' is not a list."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    (gate_dir / "quality-gates.json").write_text(
        json.dumps({"components": "not-an-array"})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c12(str(tmp_path))

    assert result.passed is False
    assert result.id == 12


# ---------------------------------------------------------------------------
# C13 tests
# ---------------------------------------------------------------------------

def test_c13_passes_when_non_fixable_empty(tmp_path: Path) -> None:
    """_check_c13 passes when drift-report.json has empty non_fixable list."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    gov_dir = tmp_path / "reports" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "drift-report.json").write_text(json.dumps({"non_fixable": []}))

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c13(str(tmp_path))

    assert result.passed is True
    assert result.id == 13
    assert result.severity == "warning"


def test_c13_fails_when_non_fixable_non_empty(tmp_path: Path) -> None:
    """_check_c13 fails when drift-report.json has non-empty non_fixable list."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    gov_dir = tmp_path / "reports" / "governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "drift-report.json").write_text(
        json.dumps({"non_fixable": [{"component": "Button", "reason": "missing spec"}]})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c13(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# C14 tests
# ---------------------------------------------------------------------------

def test_c14_passes_when_registry_valid(tmp_path: Path) -> None:
    """_check_c14 passes when validate_spec_schema returns valid=True."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    reg_dir = tmp_path / "reports"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "component-registry.json").write_text(json.dumps({"components": []}))

    with patch("daf.tools.exit_criteria_evaluator.validate_spec_schema") as mock_validate:
        mock_validate.return_value = {"valid": True, "errors": []}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c14(str(tmp_path))

    assert result.passed is True
    assert result.id == 14
    assert result.severity == "warning"


def test_c14_fails_when_registry_invalid(tmp_path: Path) -> None:
    """_check_c14 fails when validate_spec_schema returns valid=False."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    reg_dir = tmp_path / "reports"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "component-registry.json").write_text(json.dumps({"components": []}))

    with patch("daf.tools.exit_criteria_evaluator.validate_spec_schema") as mock_validate:
        mock_validate.return_value = {"valid": False, "errors": ["schema mismatch"]}
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c14(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# C15 tests
# ---------------------------------------------------------------------------

def test_c15_passes_when_no_failed_components(tmp_path: Path) -> None:
    """_check_c15 passes when no components have status='failed'."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "generation-summary.json").write_text(
        json.dumps({"components": [{"name": "Button", "status": "success"}]})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c15(str(tmp_path))

    assert result.passed is True
    assert result.id == 15
    assert result.severity == "warning"


def test_c15_fails_when_any_component_failed(tmp_path: Path) -> None:
    """_check_c15 fails when at least one component has status='failed'."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "generation-summary.json").write_text(
        json.dumps({"components": [{"name": "Button", "status": "failed"}]})
    )

    evaluator = ExitCriteriaEvaluator()
    result = evaluator._check_c15(str(tmp_path))

    assert result.passed is False


# ---------------------------------------------------------------------------
# Edge case: evaluator handles c7 subprocess timeout (duplicate of 1.40)
# ---------------------------------------------------------------------------

def test_evaluator_c7_subprocess_timeout_handled_gracefully(tmp_path: Path) -> None:
    """Same as test_c7_fails_gracefully_on_timeout — verifies no unhandled exception."""
    from daf.tools.exit_criteria_evaluator import ExitCriteriaEvaluator
    with patch(
        "daf.tools.exit_criteria_evaluator.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="tsc", timeout=30),
    ):
        evaluator = ExitCriteriaEvaluator()
        result = evaluator._check_c7(str(tmp_path))

    assert result.passed is False
