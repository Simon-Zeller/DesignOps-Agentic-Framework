# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [ ] 0.1 Create feature branch: `feat/p19-exit-criteria`
- [ ] 0.2 Verify clean working tree (`git status`)
- [ ] 0.3 Confirm `pytest` passes on current main before any changes (`uv run pytest tests/ -x -q`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### `tests/test_exit_criteria_evaluator.py` (new)

- [ ] 1.1 Add `test_evaluator_returns_15_criteria_items`: assert `len(result["criteria"]) == 15` with all delegates mocked
- [ ] 1.2 Add `test_is_complete_true_when_all_fatal_pass`: mock C1–C8 as `passed=True`; assert `result["isComplete"] is True`
- [ ] 1.3 Add `test_is_complete_false_when_one_fatal_fails`: patch C1 to `passed=False`; assert `result["isComplete"] is False`
- [ ] 1.4 Add `test_is_complete_true_when_only_warnings_fail`: C1–C8 pass, C9 fails; assert `isComplete is True`
- [ ] 1.5 Add `test_evaluator_writes_exit_criteria_json`: all mocked; assert `(tmp_path / "reports" / "exit-criteria.json").exists()`
- [ ] 1.6 Add `test_evaluator_continues_after_file_not_found`: C1 helper raises `FileNotFoundError`; assert 15 items returned, C1 `passed=False`, `isComplete=False`
- [ ] 1.7 Add `test_all_criteria_have_sequential_ids`: assert `[c["id"] for c in result["criteria"]] == list(range(1, 16))`

### C1 tests

- [ ] 1.8 Add `test_c1_passes_with_valid_token_files`: write valid JSON to `tmp_path/tokens/global.tokens.json`; call `_check_c1`; assert `passed=True`
- [ ] 1.9 Add `test_c1_fails_with_invalid_json`: write `{invalid` to token file; assert `passed=False, "detail"` contains filename
- [ ] 1.10 Add `test_c1_fails_when_tokens_dir_absent`: no `tokens/`; assert `passed=False, detail="tokens/ directory not found"`

### C2 tests

- [ ] 1.11 Add `test_c2_passes_when_dtcg_returns_empty_fatal`: mock `DtcgSchemaValidator` → `{"fatal": [], "warnings": []}`; assert `passed=True`
- [ ] 1.12 Add `test_c2_fails_when_dtcg_returns_fatal_errors`: mock → `{"fatal": ["err"], ...}`; assert `passed=False`

### C3 & C4 tests

- [ ] 1.13 Add `test_c3_passes_when_no_unresolved_refs`: mock `TokenGraphTraverser` → `{"unresolved_refs": []}`; assert `passed=True`
- [ ] 1.14 Add `test_c3_fails_with_unresolved_refs`: mock → `{"unresolved_refs": ["color.brand.missing"]}`; assert `passed=False, detail` lists the path
- [ ] 1.15 Add `test_c4_fails_with_component_unresolved_refs`

### C5 tests

- [ ] 1.16 Add `test_c5_passes_when_contrast_all_pass_true`: mock `ContrastSafePairer` → `{"all_pass": True}`; assert `passed=True`
- [ ] 1.17 Add `test_c5_fails_when_contrast_all_pass_false`: mock → `{"all_pass": False, "pairs": [...]}`; assert `passed=False`

### C6 tests

- [ ] 1.18 Add `test_c6_passes_when_all_refs_resolve`: mock `check_token_refs` → `{"all_resolved": True}`; assert `passed=True`
- [ ] 1.19 Add `test_c6_fails_with_unresolved_css_refs`: mock → `{"all_resolved": False, "unresolved": ["--x"]}`; assert `passed=False`

### C7 tests

- [ ] 1.20 Add `test_c7_passes_when_tsc_exits_0`: patch `subprocess.run` → returncode 0; assert `passed=True`
- [ ] 1.21 Add `test_c7_fails_when_tsc_exits_nonzero`: patch → returncode 2, stderr `"TS1234"`; assert `passed=False, detail` contains stderr
- [ ] 1.22 Add `test_c7_fails_gracefully_when_tsc_not_found`: patch `subprocess.run` to raise `FileNotFoundError`; assert `passed=False, detail="tsc not found"`
- [ ] 1.23 Add `test_c7_fails_gracefully_on_timeout`: patch to raise `subprocess.TimeoutExpired`; assert `passed=False`

### C8 tests

- [ ] 1.24 Add `test_c8_passes_when_dep_resolver_succeeds`: mock `DependencyResolver` → `{"success": True}`; assert `passed=True`
- [ ] 1.25 Add `test_c8_fails_when_dep_resolver_fails`: mock → `{"success": False, "errors": ["npm ERR"]}`; assert `passed=False`

### C9–C15 tests

- [ ] 1.26 Add `test_c9_passes_when_all_pass_true_in_summary`: write `{"test_results": {"all_pass": true}}` to `reports/generation-summary.json`; assert `passed=True, severity="warning"`
- [ ] 1.27 Add `test_c9_fails_when_summary_absent`
- [ ] 1.28 Add `test_c10_passes_when_no_hardcoded_colors`: mock `AstPatternMatcher` → `{"targets": []}`; assert `passed=True`
- [ ] 1.29 Add `test_c10_fails_with_hardcoded_color_targets`: mock → `{"targets": [{"type": "hardcoded_color", ...}]}`
- [ ] 1.30 Add `test_c12_passes_when_all_scores_above_70`: write quality-gates.json with scores 85, 90; assert `passed=True`
- [ ] 1.31 Add `test_c12_fails_when_any_score_below_70`: write quality-gates.json with score 60; assert `passed=False`
- [ ] 1.32 Add `test_c12_fails_when_quality_gates_absent`
- [ ] 1.33 Add `test_c13_passes_when_non_fixable_empty`: write `drift-report.json` with `{"non_fixable": []}`; assert `passed=True`
- [ ] 1.34 Add `test_c13_fails_when_non_fixable_non_empty`
- [ ] 1.35 Add `test_c14_passes_when_registry_valid`: mock `validate_spec_schema` → `{"valid": True}`; assert `passed=True`
- [ ] 1.36 Add `test_c14_fails_when_registry_invalid`
- [ ] 1.37 Add `test_c15_passes_when_no_failed_components`: write summary with all `status: "success"`; assert `passed=True`
- [ ] 1.38 Add `test_c15_fails_when_any_component_failed`: write summary with one `status: "failed"`; assert `passed=False`

### Edge case tests

- [ ] 1.39 Add `test_c12_handles_malformed_components_field`: write `{"components": "not-an-array"}`; assert `passed=False`, no exception
- [ ] 1.40 Add `test_evaluator_c7_subprocess_timeout_handled_gracefully`

### `tests/test_exit_criteria_agent.py` (new)

- [ ] 1.41 Add `test_create_exit_criteria_agent_returns_agent`: assert `isinstance(agent, crewai.Agent)`
- [ ] 1.42 Add `test_exit_criteria_agent_has_exactly_two_tools`: assert `len(agent.tools) == 2`

### Crew wiring tests

- [ ] 1.43 In `tests/test_governance_crew.py` (existing file, modify): add `test_governance_crew_includes_exit_criteria_task`: assert a task with description containing `"exit-criteria.json"` is in `crew.tasks`
- [ ] 1.44 In `tests/test_release_crew.py` (existing file, modify): add `test_t6_references_exit_criteria_json`: assert `t6_final_status.description` contains `"exit-criteria.json"`

- [ ] 1.45 Verify all new tests FAIL (red phase confirmation — `uv run pytest tests/test_exit_criteria_evaluator.py tests/test_exit_criteria_agent.py -x -q`)
- [ ] 1.46 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p19-exit-criteria"`

## 2. Implementation (TDD — Green Phase)

### 2a. `ExitCriteriaEvaluator` tool

- [ ] 2.1 Create `src/daf/tools/exit_criteria_evaluator.py`:
  - Define `CriterionResult` dataclass with fields `id`, `description`, `severity`, `passed`, `detail`
  - Implement `_check_c1(output_dir)` — json.loads scan of `tokens/*.tokens.json`
  - Implement `_check_c2(output_dir)` — delegates to `DtcgSchemaValidator._run()`
  - Implement `_check_c3(output_dir)` — delegates to `TokenGraphTraverser._run()` (semantic layer)
  - Implement `_check_c4(output_dir)` — delegates to `TokenGraphTraverser._run()` (component layer)
  - Implement `_check_c5(output_dir)` — delegates to `ContrastSafePairer._run()`; reads `all_pass`
  - Implement `_check_c6(output_dir)` — delegates to `check_token_refs()` from `token_ref_checker`
  - Implement `_check_c7(output_dir)` — `subprocess.run(["tsc", "--noEmit"])` in output dir
  - Implement `_check_c8(output_dir)` — delegates to `DependencyResolver._run()`
  - Implement `_check_c9(output_dir)` — reads `reports/generation-summary.json`, checks `test_results.all_pass`
  - Implement `_check_c10(output_dir)` — delegates to `AstPatternMatcher._run()`; filters `hardcoded_color` targets
  - Implement `_check_c11(output_dir)` — reads component registry, calls `extract_a11y_attributes` per interactive component
  - Implement `_check_c12(output_dir)` — reads `reports/governance/quality-gates.json`; checks all scores ≥70
  - Implement `_check_c13(output_dir)` — reads `reports/governance/drift-report.json`; checks `non_fixable` empty
  - Implement `_check_c14(output_dir)` — reads `reports/component-registry.json`; calls `validate_spec_schema`
  - Implement `_check_c15(output_dir)` — reads `reports/generation-summary.json`; checks no `status: "failed"` components
  - Implement `ExitCriteriaEvaluator(BaseTool)._run(output_dir)` — runs all 15, aggregates, writes JSON report
- [ ] 2.2 Verify tests 1.1–1.40 pass

### 2b. `ExitCriteriaAgent` factory

- [ ] 2.3 Create `src/daf/agents/exit_criteria.py`:
  - Implement `create_exit_criteria_agent(model, output_dir) -> Agent`
  - Role: `"Exit Criteria Evaluator"`
  - Tools: `[ExitCriteriaEvaluator(output_dir=output_dir), ReportWriter()]`
  - LLM: `model` (caller provides Haiku-tier model string)
  - `verbose=False`
- [ ] 2.4 Verify tests 1.41–1.42 pass

### 2c. Governance Crew wiring

- [ ] 2.5 In `src/daf/crews/governance.py`:
  - Import `create_exit_criteria_agent` from `daf.agents.exit_criteria`
  - Add `agent_exit_criteria = create_exit_criteria_agent(model, output_dir)` after agents 26–30
  - Add `t5_exit_criteria = Task(description=..., expected_output="reports/exit-criteria.json written", agent=agent_exit_criteria)` after `t4_quality_gate`
  - Add `t5_exit_criteria` to the `tasks` list in the `Crew(...)` constructor, after `t4_quality_gate`
- [ ] 2.6 Verify test 1.43 passes

### 2d. Release Crew `t6_final_status` update

- [ ] 2.7 In `src/daf/crews/release.py`, update the `t6_final_status` Task `description` to:
  - Reference `reports/exit-criteria.json` as the input source
  - Define the three-way mapping: `isComplete: true` + no warning failures → `final_status: "success"`; `isComplete: true` + warning failures → `final_status: "partial"`; `isComplete: false` → `final_status: "failed"`
- [ ] 2.8 Verify test 1.44 passes

- [ ] 2.9 Verify ALL tests pass (`uv run pytest tests/ -x -q`)
- [ ] 2.10 **Git checkpoint:** `git add -A && git commit -m "feat: implement exit criteria evaluator and agent wiring (p19)"`

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Review `exit_criteria_evaluator.py` — ensure each `_check_cN` is ≤20 lines; extract shared file-reading helpers if needed
- [ ] 3.2 Verify `_check_c7` and `_check_c8` subprocess/tool delegation is not duplicating logic from `DependencyResolver`
- [ ] 3.3 Confirm the `CriterionResult` dataclass has proper `__repr__` and is importable from `daf.tools.exit_criteria_evaluator`
- [ ] 3.4 Ensure all tests still pass after refactor (`uv run pytest tests/ -x -q`)
- [ ] 3.5 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up exit criteria evaluator (p19)"`

## 4. Integration & Quality

- [ ] 4.1 Run `uv run ruff check src/daf/tools/exit_criteria_evaluator.py src/daf/agents/exit_criteria.py src/daf/crews/governance.py src/daf/crews/release.py`
- [ ] 4.2 Run `uv run pyright src/daf/tools/exit_criteria_evaluator.py src/daf/agents/exit_criteria.py`
- [ ] 4.3 Fix all lint and type errors — zero warnings policy
- [ ] 4.4 Run full test suite: `uv run pytest tests/ -q`
- [ ] 4.5 Verify no regressions in existing tests (especially `test_governance_crew.py`, `test_release_crew.py`, `test_quality_gate.py`)
- [ ] 4.6 Check test coverage: `uv run pytest --cov=daf.tools.exit_criteria_evaluator --cov=daf.agents.exit_criteria --cov-report=term-missing tests/test_exit_criteria_evaluator.py tests/test_exit_criteria_agent.py` — must show ≥80% line coverage
- [ ] 4.7 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p19-exit-criteria"` (skip if no changes)

## 5. Final Verification & Push

- [ ] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [ ] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [ ] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [ ] 5.4 Push feature branch (`git push origin feat/p19-exit-criteria`)

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p19-exit-criteria`)
- [ ] 6.3 Push main (`git push origin main`)
- [ ] 6.4 Delete local feature branch (`git branch -d feat/p19-exit-criteria`)
- [ ] 6.5 Delete remote feature branch (`git push origin --delete feat/p19-exit-criteria`)
- [ ] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
