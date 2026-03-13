# TDD Plan: p19-exit-criteria

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

- **Framework:** pytest (all existing DAF tests use pytest)
- **Type:** Primarily unit tests; all subprocess calls (tsc, npm) are mocked using `unittest.mock.patch`
- **Approach:** Each of the 15 criterion helper functions is tested in isolation by directly calling the private `_check_cN` helpers (exposed via module-level test access). The `ExitCriteriaEvaluator._run` is tested end-to-end with all delegates mocked.
- **Fixtures:** `tmp_path` (pytest built-in) creates minimal output directory trees with the files each criterion needs.
- **Coverage target:** ≥80% line coverage on `exit_criteria_evaluator.py` and `agents/exit_criteria.py`.

---

## Test Cases

### ExitCriteriaEvaluator — Aggregation & report writing

#### Test: evaluator returns 15 criteria items

- **Maps to:** EX-01 → Scenario "All 15 criteria pass"
- **Type:** unit
- **Given:** All 15 check helpers return `passed=True`; all delegates are mocked
- **When:** `ExitCriteriaEvaluator()._run(output_dir=str(tmp_path))` is called
- **Then:** Result `criteria` list has exactly 15 items with `id` values 1–15
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: isComplete is True when all Fatal pass

- **Maps to:** EX-01 → Scenario "All 15 criteria pass"
- **Type:** unit
- **Given:** C1–C8 all return `passed=True`; C9–C15 return `passed=True`; delegates mocked
- **When:** `ExitCriteriaEvaluator()._run(...)` is called
- **Then:** Result `isComplete` is `True`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: isComplete is False when one Fatal fails

- **Maps to:** EX-01 → Scenario "One Fatal criterion fails"
- **Type:** unit
- **Given:** C1 helper is patched to return `passed=False`; all other criteria pass
- **When:** `ExitCriteriaEvaluator()._run(...)` is called
- **Then:** Result `isComplete` is `False`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: isComplete is True when only Warning criteria fail

- **Maps to:** EX-01 → Scenario "Only Warning criteria fail"
- **Type:** unit
- **Given:** C1–C8 all return `passed=True`; C9 returns `passed=False, severity="warning"`
- **When:** `ExitCriteriaEvaluator()._run(...)` is called
- **Then:** Result `isComplete` is `True`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: evaluator writes exit-criteria.json to disk

- **Maps to:** EX-01 acceptance criterion "reports/exit-criteria.json is written to disk"
- **Type:** unit
- **Given:** All delegates mocked to pass; `tmp_path` provided as output_dir
- **When:** `ExitCriteriaEvaluator()._run(output_dir=str(tmp_path))` is called
- **Then:** `tmp_path / "reports" / "exit-criteria.json"` exists and contains valid JSON with `isComplete` key
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: evaluator continues evaluating after one helper raises FileNotFoundError

- **Maps to:** EX-01 acceptance criteria (graceful degradation design decision)
- **Type:** unit
- **Given:** C1 helper raises `FileNotFoundError`; all others return `passed=True`
- **When:** `ExitCriteriaEvaluator()._run(...)` is called
- **Then:** 15 criteria items returned; C1 has `passed=False` and non-empty `detail`; result has `isComplete=False`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C1 — Token JSON parses without error

#### Test: c1 passes with valid token files

- **Maps to:** EX-02 → Scenario "Valid token files"
- **Type:** unit
- **Given:** `tmp_path/tokens/global.tokens.json` contains a valid JSON object
- **When:** `_check_c1(output_dir)` is called
- **Then:** Returns `CriterionResult(id=1, passed=True, severity="fatal", detail="")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c1 fails with invalid JSON

- **Maps to:** EX-02 → Scenario "Invalid JSON in one token file"
- **Type:** unit
- **Given:** `tmp_path/tokens/broken.tokens.json` contains `{invalid`
- **When:** `_check_c1(output_dir)` is called
- **Then:** Returns `CriterionResult(id=1, passed=False, ...)` with `detail` containing the filename
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c1 fails when tokens directory is absent

- **Maps to:** EX-02 acceptance criterion "tokens/ directory not found"
- **Type:** unit
- **Given:** `tmp_path` has no `tokens/` subdirectory
- **When:** `_check_c1(output_dir)` is called
- **Then:** Returns `CriterionResult(id=1, passed=False, detail="tokens/ directory not found")`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C2 — DTCG schema conformance

#### Test: c2 passes when DtcgSchemaValidator returns empty fatal list

- **Maps to:** EX-03 acceptance criterion "DtcgSchemaValidator returns fatal: []"
- **Type:** unit
- **Given:** `DtcgSchemaValidator` is mocked to return `{"fatal": [], "warnings": []}`
- **When:** `_check_c2(output_dir)` is called
- **Then:** Returns `CriterionResult(id=2, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c2 fails when DtcgSchemaValidator returns non-empty fatal list

- **Maps to:** EX-03 acceptance criterion "fatal list non-empty"
- **Type:** unit
- **Given:** `DtcgSchemaValidator` is mocked to return `{"fatal": ["missing $type at token.x"], "warnings": []}`
- **When:** `_check_c2(output_dir)` is called
- **Then:** Returns `CriterionResult(id=2, passed=False, ...)` with `detail` containing the error
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C3 & C4 — Token reference resolution

#### Test: c3 passes when TokenGraphTraverser returns empty unresolved_refs

- **Maps to:** EX-04 → C3 happy path
- **Type:** unit
- **Given:** `TokenGraphTraverser` mocked to return `{"tokens": [...], "unresolved_refs": []}`
- **When:** `_check_c3(output_dir)` is called
- **Then:** Returns `CriterionResult(id=3, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c3 fails when unresolved_refs is non-empty

- **Maps to:** EX-04 → C3 failure
- **Type:** unit
- **Given:** `TokenGraphTraverser` mocked to return `{"unresolved_refs": ["color.brand.missing"]}`
- **When:** `_check_c3(output_dir)` is called
- **Then:** Returns `CriterionResult(id=3, passed=False, ...)` with `detail` listing the unresolved paths
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c4 follows same logic for component-scoped tokens

- **Maps to:** EX-04 → C4 parity with C3
- **Type:** unit
- **Given:** `TokenGraphTraverser` mocked with unresolved component-scoped refs
- **When:** `_check_c4(output_dir)` is called
- **Then:** Returns `CriterionResult(id=4, passed=False, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C5 — WCAG contrast

#### Test: c5 passes when ContrastSafePairer returns all_pass True

- **Maps to:** EX-05 → happy path
- **Type:** unit
- **Given:** `ContrastSafePairer` mocked to return `{"all_pass": True, "pairs": []}`
- **When:** `_check_c5(output_dir)` is called
- **Then:** Returns `CriterionResult(id=5, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c5 fails when ContrastSafePairer returns all_pass False

- **Maps to:** EX-05 → failure
- **Type:** unit
- **Given:** `ContrastSafePairer` mocked to return `{"all_pass": False, "pairs": [{"fg": "#fff", "bg": "#eee", "ratio": 1.2, "pass": False}]}`
- **When:** `_check_c5(output_dir)` is called
- **Then:** Returns `CriterionResult(id=5, passed=False, ...)` with `detail` summarising failing pairs
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C6 — CSS custom properties

#### Test: c6 passes when all CSS refs resolve

- **Maps to:** EX-06 → happy path
- **Type:** unit
- **Given:** `check_token_refs` mocked to return `{"all_resolved": True, "unresolved": []}`
- **When:** `_check_c6(output_dir)` is called
- **Then:** Returns `CriterionResult(id=6, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c6 fails with unresolved CSS references

- **Maps to:** EX-06 → failure
- **Type:** unit
- **Given:** `check_token_refs` mocked to return `{"all_resolved": False, "unresolved": ["--color-brand-primary"]}`
- **When:** `_check_c6(output_dir)` is called
- **Then:** Returns `CriterionResult(id=6, passed=False, detail="unresolved: ['--color-brand-primary']")`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C7 — TypeScript compilation

#### Test: c7 passes when tsc exits 0

- **Maps to:** EX-07 → happy path
- **Type:** unit
- **Given:** `subprocess.run` is mocked to return exit code 0 and empty stderr
- **When:** `_check_c7(output_dir)` is called
- **Then:** Returns `CriterionResult(id=7, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c7 fails when tsc exits non-zero

- **Maps to:** EX-07 → failure
- **Type:** unit
- **Given:** `subprocess.run` mocked to return exit code 2 and stderr `"error TS1234: ..."`
- **When:** `_check_c7(output_dir)` is called
- **Then:** Returns `CriterionResult(id=7, passed=False, detail)` with `detail` containing the stderr excerpt
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c7 fails gracefully when tsc is not installed

- **Maps to:** EX-07 → "tsc not installed" edge case
- **Type:** unit
- **Given:** `subprocess.run` raises `FileNotFoundError`
- **When:** `_check_c7(output_dir)` is called
- **Then:** Returns `CriterionResult(id=7, passed=False, detail="tsc not found")`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C8 — npm build

#### Test: c8 passes when DependencyResolver returns success True

- **Maps to:** EX-08 → happy path
- **Type:** unit
- **Given:** `DependencyResolver` mocked to return `{"success": True, "errors": []}`
- **When:** `_check_c8(output_dir)` is called
- **Then:** Returns `CriterionResult(id=8, passed=True, severity="fatal")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c8 fails when DependencyResolver returns success False

- **Maps to:** EX-08 → failure
- **Type:** unit
- **Given:** `DependencyResolver` mocked to return `{"success": False, "errors": ["npm ERR! missing peer dep"]}`
- **When:** `_check_c8(output_dir)` is called
- **Then:** Returns `CriterionResult(id=8, passed=False, ...)` with `detail` containing the error
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### C9–C15 — Warning criteria

#### Test: c9 passes when generation-summary.json has all_pass True

- **Maps to:** EX-09 → happy path
- **Type:** unit
- **Given:** `tmp_path/reports/generation-summary.json` contains `{"test_results": {"all_pass": true}}`
- **When:** `_check_c9(output_dir)` is called
- **Then:** Returns `CriterionResult(id=9, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c9 fails when generation-summary.json is absent

- **Maps to:** EX-09 acceptance criterion "absent file"
- **Type:** unit
- **Given:** `tmp_path` has no `reports/generation-summary.json`
- **When:** `_check_c9(output_dir)` is called
- **Then:** Returns `CriterionResult(id=9, passed=False, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c10 passes when AstPatternMatcher returns no hardcoded colors

- **Maps to:** EX-10 → happy path
- **Type:** unit
- **Given:** `AstPatternMatcher` mocked to return `{"targets": []}`
- **When:** `_check_c10(output_dir)` is called
- **Then:** Returns `CriterionResult(id=10, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c10 fails when hardcoded_color targets found

- **Maps to:** EX-10 → failure
- **Type:** unit
- **Given:** `AstPatternMatcher` mocked to return `{"targets": [{"type": "hardcoded_color", "pattern": "#333", "file": "Button.tsx", "line": 12}]}`
- **When:** `_check_c10(output_dir)` is called
- **Then:** Returns `CriterionResult(id=10, passed=False, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c12 passes when quality-gates.json shows all scores ≥70

- **Maps to:** EX-12 → happy path
- **Type:** unit
- **Given:** `tmp_path/reports/governance/quality-gates.json` has all component scores `>= 70`
- **When:** `_check_c12(output_dir)` is called
- **Then:** Returns `CriterionResult(id=12, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c12 fails when any component score is below 70

- **Maps to:** EX-12 → failure
- **Type:** unit
- **Given:** `quality-gates.json` has one component with `score: 60`
- **When:** `_check_c12(output_dir)` is called
- **Then:** Returns `CriterionResult(id=12, passed=False, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c13 passes when drift report has empty non_fixable list

- **Maps to:** EX-13 → happy path
- **Type:** unit
- **Given:** `tmp_path/reports/governance/drift-report.json` has `{"non_fixable": []}`
- **When:** `_check_c13(output_dir)` is called
- **Then:** Returns `CriterionResult(id=13, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c14 passes when component-registry.json is valid

- **Maps to:** EX-14 → happy path
- **Type:** unit
- **Given:** `validate_spec_schema` mocked to return `{"valid": True, "errors": []}`
- **When:** `_check_c14(output_dir)` is called
- **Then:** Returns `CriterionResult(id=14, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c15 passes when no failed components in generation summary

- **Maps to:** EX-15 → happy path
- **Type:** unit
- **Given:** `tmp_path/reports/generation-summary.json` has `{"components": [{"name": "Button", "status": "success"}]}`
- **When:** `_check_c15(output_dir)` is called
- **Then:** Returns `CriterionResult(id=15, passed=True, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c15 fails when any component has status failed

- **Maps to:** EX-15 → failure
- **Type:** unit
- **Given:** `generation-summary.json` has one component with `status: "failed"`
- **When:** `_check_c15(output_dir)` is called
- **Then:** Returns `CriterionResult(id=15, passed=False, severity="warning")`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

### ExitCriteriaAgent factory

#### Test: create_exit_criteria_agent returns a crewai.Agent

- **Maps to:** EX-16 acceptance criteria
- **Type:** unit
- **Given:** Valid model string and output_dir string
- **When:** `create_exit_criteria_agent("claude-3-haiku-20240307", "/tmp/out")` is called
- **Then:** Returns an instance of `crewai.Agent`
- **File:** `tests/test_exit_criteria_agent.py`

#### Test: agent has exactly two tools

- **Maps to:** EX-16 acceptance criteria "exactly two tools"
- **Type:** unit
- **Given:** Agent created with `create_exit_criteria_agent(...)`
- **When:** `agent.tools` is inspected
- **Then:** `len(agent.tools) == 2`; tool names are `"exit_criteria_evaluator"` and one of the `ReportWriter` variants
- **File:** `tests/test_exit_criteria_agent.py`

---

### Governance Crew wiring

#### Test: governance crew includes t5_exit_criteria task

- **Maps to:** EX-17 acceptance criteria
- **Type:** unit
- **Given:** `create_governance_crew` is called with a model and output_dir
- **When:** The returned `Crew.tasks` list is inspected
- **Then:** A task with description containing `"exit-criteria.json"` or `"exit criteria"` is present after the quality gate task
- **File:** `tests/test_governance_crew.py` (modified)

---

### Release Crew t6_final_status

#### Test: t6_final_status task description references exit-criteria.json

- **Maps to:** EX-18 acceptance criteria
- **Type:** unit
- **Given:** `create_release_crew` is called
- **When:** Task `t6_final_status` description is inspected
- **Then:** The description string contains `"exit-criteria.json"`
- **File:** `tests/test_release_crew.py` (modified)

---

## Edge Case Tests

#### Test: evaluator handles zero token files in tokens/ directory

- **Maps to:** EX-02 edge case
- **Type:** unit
- **Given:** `tmp_path/tokens/` exists but is empty
- **When:** `_check_c1(output_dir)` is called
- **Then:** Returns `passed=True` (no files to fail = vacuously true) OR `passed=False` with `detail: "no token files found"` — implementation choice, but behavior must be consistent
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: evaluator handles malformed quality-gates.json (non-array components)

- **Maps to:** EX-12 error case
- **Type:** unit
- **Given:** `quality-gates.json` contains `{"components": "not-an-array"}`
- **When:** `_check_c12(output_dir)` is called
- **Then:** Returns `CriterionResult(id=12, passed=False, severity="warning", detail)` — no unhandled exception
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: c7 subprocess timeout is handled gracefully

- **Maps to:** EX-07 "tsc not installed" edge case (extended)
- **Type:** unit
- **Given:** `subprocess.run` raises `subprocess.TimeoutExpired`
- **When:** `_check_c7(output_dir)` is called
- **Then:** Returns `CriterionResult(id=7, passed=False, detail="tsc timed out")`
- **File:** `tests/test_exit_criteria_evaluator.py`

#### Test: all criteria have sequential IDs 1–15 in output

- **Maps to:** EX-01 acceptance criterion "id values 1–15"
- **Type:** unit
- **When:** `ExitCriteriaEvaluator()._run(...)` is called with all delegates mocked
- **Then:** `[c["id"] for c in result["criteria"]] == list(range(1, 16))`
- **File:** `tests/test_exit_criteria_evaluator.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage (`exit_criteria_evaluator.py`) | ≥80% | PRD quality gate requirement |
| Line coverage (`agents/exit_criteria.py`) | ≥80% | PRD quality gate requirement |
| Branch coverage (criterion helpers) | ≥70% | Covers both pass/fail branches per criterion |
| A11y rules passing | 100% critical | Zero critical a11y violations (no UI in this change) |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_exit_criteria_evaluator.py` | new | All 15 criterion helpers + evaluator aggregation + report writing |
| `tests/test_exit_criteria_agent.py` | new | Agent factory assertions (tools, model, role) |
| `tests/test_governance_crew.py` | modified | Assert `t5_exit_criteria` is present in task list |
| `tests/test_release_crew.py` | modified | Assert `t6_final_status` references `exit-criteria.json` |
