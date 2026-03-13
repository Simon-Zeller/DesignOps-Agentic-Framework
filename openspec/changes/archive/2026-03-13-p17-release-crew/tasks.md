# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p17-release-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `ANTHROPIC_API_KEY` is set in environment for integration test runs

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### Crew factory tests
- [x] 1.1 Create `tests/test_release_crew.py` with:
  - `test_crew_raises_runtime_error_when_gate_report_missing`
  - `test_crew_returns_crewai_crew_when_gate_report_exists`
  - `test_crew_has_four_agents_and_six_tasks`
  - `test_crew_creates_docs_and_codemods_directories`
  - `test_crew_does_not_include_rollback_agent`

### Agent factory tests
- [x] 1.2 Create `tests/test_semver_agent.py` — factory return type, role keyword, Haiku model, tools (`GateStatusReader`, `VersionCalculator`)
- [x] 1.3 Create `tests/test_release_changelog_agent.py` — factory return type, role keyword, Sonnet model, tools (`ComponentInventoryReader`, `QualityReportParser`, `ProseGenerator`)
- [x] 1.4 Create `tests/test_codemod_agent.py` — factory return type, role keyword, Haiku model, tools (`ASTPatternMatcher`, `CodemodTemplateGenerator`, `ExampleSuiteBuilder`)
- [x] 1.5 Create `tests/test_publish_agent.py` — factory return type, role keyword, Haiku model, tools (`PackageJsonGenerator`, `DependencyResolver`, `TestResultParser`, `ReportWriter`)
- [x] 1.6 Create `tests/test_rollback_agent.py` — factory return type, role keyword, Haiku model, tools (`CheckpointCreator`, `RestoreExecutor`, `RollbackReporter`), exclusion from crew

### Tool tests
- [x] 1.7 Create `tests/test_gate_status_reader.py`:
  - `test_returns_pass_fail_counts_from_valid_json`
  - `test_returns_safe_default_when_file_absent`
  - `test_returns_warning_on_fallback`
- [x] 1.8 Create `tests/test_version_calculator.py`:
  - `test_returns_v1_0_0_when_all_fatal_gates_pass`
  - `test_returns_v0_x_0_when_any_fatal_gate_fails`
  - `test_returns_experimental_on_malformed_input`
- [x] 1.9 Create `tests/test_component_inventory_reader.py`:
  - `test_returns_component_list_from_specs`
  - `test_returns_empty_list_when_specs_absent`
  - `test_handles_malformed_yaml_gracefully`
- [x] 1.10 Create `tests/test_quality_report_parser.py`:
  - `test_parses_gate_json_into_structured_summary`
  - `test_handles_missing_report_gracefully`
- [x] 1.11 Create `tests/test_ast_pattern_matcher.py`:
  - `test_detects_raw_html_elements_in_tsx`
  - `test_detects_hardcoded_hex_colors_in_tsx`
  - `test_returns_empty_targets_when_src_absent`
- [x] 1.12 Create `tests/test_codemod_template_generator.py`:
  - `test_generates_before_and_after_snippets`
  - `test_output_is_markdown_string`
- [x] 1.13 Create `tests/test_example_suite_builder.py`:
  - `test_writes_codemod_files_to_docs_codemods`
  - `test_writes_readme_when_no_targets_exist`
- [x] 1.14 Create `tests/test_package_json_generator.py`:
  - `test_generates_valid_package_json_with_required_fields`
  - `test_version_field_strips_v_prefix`
  - `test_experimental_version_is_handled`
- [x] 1.15 Create `tests/test_dependency_resolver.py`:
  - `test_returns_npm_unavailable_when_npm_not_on_path`
  - `test_returns_success_when_command_exits_0`
  - `test_returns_failed_dict_when_command_exits_non_zero`
  - `test_never_raises_unhandled_exception`
- [x] 1.16 Create `tests/test_test_result_parser.py`:
  - `test_parses_passing_test_output`
  - `test_parses_failing_test_output`
  - `test_handles_empty_stdout`
- [x] 1.17 Create `tests/test_checkpoint_creator.py`:
  - `test_snapshot_creates_checkpoint_directory`
  - `test_snapshot_copies_output_dir_contents`
  - `test_creates_checkpoints_dir_if_absent`
- [x] 1.18 Create `tests/test_restore_executor.py`:
  - `test_restore_copies_checkpoint_back_to_output_dir`
  - `test_raises_file_not_found_when_snapshot_missing`
- [x] 1.19 Create `tests/test_rollback_reporter.py`:
  - `test_writes_rollback_log_json`
  - `test_rollback_log_contains_restored_phase_and_reason`

- [x] 1.20 Verify **all new tests FAIL** (`pytest tests/test_release_crew.py tests/test_semver_agent.py tests/test_release_changelog_agent.py tests/test_codemod_agent.py tests/test_publish_agent.py tests/test_rollback_agent.py tests/test_gate_status_reader.py tests/test_version_calculator.py -x`)
- [x] 1.21 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p17-release-crew"`

## 2. Implementation (TDD — Green Phase)

### 2A. Deterministic Tools

- [x] 2.1 Create `src/daf/tools/gate_status_reader.py` — `GateStatusReader(BaseTool)`: reads `reports/governance/quality-gates.json`, returns `{"fatal_passed": N, "fatal_failed": N, "warning_passed": N, "warning_failed": N, "gates": [...]}`, returns all-zero safe default when file absent
- [x] 2.2 Create `src/daf/tools/version_calculator.py` — `VersionCalculator(BaseTool)`: derives semver string from gate pass/fail dict; `v1.0.0` when `fatal_failed == 0`; `v0.1.0` otherwise; `v0.1.0-experimental` on malformed input
- [x] 2.3 Create `src/daf/tools/component_inventory_reader.py` — `ComponentInventoryReader(BaseTool)`: reads `specs/*.spec.yaml` and `reports/` to build component list with status and quality score; skips malformed YAML files gracefully; returns `{"components": []}` when specs absent
- [x] 2.4 Create `src/daf/tools/quality_report_parser.py` — `QualityReportParser(BaseTool)`: reads quality gate and generation reports; returns structured `{"passed_gates": [...], "failed_gates": [...], "warnings": [...]}`
- [x] 2.5 Create `src/daf/tools/ast_pattern_matcher.py` — `ASTPatternMatcher(BaseTool)`: regex/heuristic scan of `src/components/**/*.tsx` and `src/primitives/**/*.tsx`; detects raw HTML elements (e.g. `<button`, `<input`) and hardcoded hex/rgb colors; returns `{"targets": [{type, pattern, file, line}]}` or `{"targets": []}` when src absent
- [x] 2.6 Create `src/daf/tools/codemod_template_generator.py` — `CodemodTemplateGenerator(BaseTool)`: given a migration target dict `{"element": "button", "ds_component": "Button"}`, returns a Markdown string with "before" and "after" code blocks
- [x] 2.7 Create `src/daf/tools/example_suite_builder.py` — `ExampleSuiteBuilder(BaseTool)`: writes codemod Markdown files to `docs/codemods/`; writes `docs/codemods/README.md` stating no migrations needed when targets list is empty
- [x] 2.8 Create `src/daf/tools/package_json_generator.py` — `PackageJsonGenerator(BaseTool)`: assembles `package.json` from input dict; strips `v` prefix from version; ensures `name`, `version`, `main`, `types`, `exports`, `peerDependencies`, `scripts` fields are present; writes file to `output_dir/package.json`
- [x] 2.9 Create `src/daf/tools/dependency_resolver.py` — `DependencyResolver(BaseTool)`: wraps `subprocess.run` for `npm install`, `tsc --noEmit`, `npm test`; returns `{"status": "npm_unavailable"}` when `npm` not on `$PATH` (catches `FileNotFoundError` and `OSError`); returns `{"status": "success", "stdout": "..."}` on exit code 0; returns `{"status": "failed", "exit_code": N, "stderr": "..."}` on non-zero exit; uses configurable `cwd` from `output_dir`
- [x] 2.10 Create `src/daf/tools/test_result_parser.py` — `TestResultParser(BaseTool)`: parses Vitest/pytest stdout into `{"passed": N, "failed": N, "skipped": N}`; returns all-zero dict on empty or unrecognised input
- [x] 2.11 Create `src/daf/tools/checkpoint_creator.py` — `CheckpointCreator(BaseTool)`: accepts phase name; creates `checkpoints/<phase_name>/` inside `output_dir` if absent; copies current `output_dir` contents into it (excluding `checkpoints/` itself to avoid recursion)
- [x] 2.12 Create `src/daf/tools/restore_executor.py` — `RestoreExecutor(BaseTool)`: accepts phase name; raises `FileNotFoundError` if `checkpoints/<phase_name>/` absent; copies checkpoint contents back into `output_dir`, overwriting current files
- [x] 2.13 Create `src/daf/tools/rollback_reporter.py` — `RollbackReporter(BaseTool)`: accepts a dict with `restored_phase`, `failed_crew`, `reason`; writes `reports/rollback-log.json`; appends to existing log if present
- [x] 2.14 Verify tool tests pass (`pytest tests/test_gate_status_reader.py tests/test_version_calculator.py tests/test_component_inventory_reader.py tests/test_quality_report_parser.py tests/test_ast_pattern_matcher.py tests/test_codemod_template_generator.py tests/test_example_suite_builder.py tests/test_package_json_generator.py tests/test_dependency_resolver.py tests/test_test_result_parser.py tests/test_checkpoint_creator.py tests/test_restore_executor.py tests/test_rollback_reporter.py`)
- [x] 2.15 **Git checkpoint:** `git add -A && git commit -m "feat(release): implement deterministic tools for Release Crew"`

### 2B. Agent Factories

- [x] 2.16 Create `src/daf/agents/semver.py` — `create_semver_agent(model, output_dir) → crewai.Agent`; role "Version calculator"; goal per PRD §4.8; tools: `GateStatusReader`, `VersionCalculator`; model: Haiku
- [x] 2.17 Create `src/daf/agents/release_changelog.py` — `create_release_changelog_agent(model, output_dir) → crewai.Agent`; role "Release inventory author"; goal per PRD §4.8; tools: `ComponentInventoryReader`, `QualityReportParser`, `ProseGenerator`; model: Sonnet
- [x] 2.18 Create `src/daf/agents/codemod.py` — `create_codemod_agent(model, output_dir) → crewai.Agent`; role "Adoption helper generator"; goal per PRD §4.8; tools: `ASTPatternMatcher`, `CodemodTemplateGenerator`, `ExampleSuiteBuilder`; model: Haiku
- [x] 2.19 Create `src/daf/agents/publish.py` — `create_publish_agent(model, output_dir) → crewai.Agent`; role "Package assembler and final validator"; goal per PRD §4.8; tools: `PackageJsonGenerator`, `DependencyResolver`, `TestResultParser`, `ReportWriter`; model: Haiku
- [x] 2.20 Rewrite `src/daf/agents/rollback.py` — `create_rollback_agent(model, output_dir) → crewai.Agent`; role "Generation checkpoint manager"; goal per PRD §4.8; tools: `CheckpointCreator`, `RestoreExecutor`, `RollbackReporter`; model: Haiku; replace existing stub implementation
- [x] 2.21 Update `src/daf/agents/__init__.py` — export `create_semver_agent`, `create_release_changelog_agent`, `create_codemod_agent`, `create_publish_agent`, and updated `create_rollback_agent`
- [x] 2.22 Verify agent tests pass (`pytest tests/test_semver_agent.py tests/test_release_changelog_agent.py tests/test_codemod_agent.py tests/test_publish_agent.py tests/test_rollback_agent.py`)
- [x] 2.23 **Git checkpoint:** `git add -A && git commit -m "feat(release): implement agent factories 36-40"`

### 2C. Crew Factory

- [x] 2.24 Rewrite `src/daf/crews/release.py`:
  - Remove `StubCrew` import and stub `_run` function
  - Add pre-flight guard: `RuntimeError` if `reports/governance/quality-gates.json` absent
  - Ensure `docs/` and `docs/codemods/` directories are created if absent
  - Instantiate agents 36–39 with correct model tier strings (Agent 40 is NOT included in crew agents list)
  - Define tasks T1–T6 with sequential `context` chaining
  - Return `crewai.Crew(agents=[agent36, agent37, agent38, agent39], tasks=[t1, t2, t3, t4, t5, t6], verbose=False)`
- [x] 2.25 Update `src/daf/tools/__init__.py` — export all new tool classes
- [x] 2.26 Verify crew tests pass (`pytest tests/test_release_crew.py`)
- [x] 2.27 Run all new tests together — confirm green:
  ```
  pytest tests/test_release_crew.py tests/test_semver_agent.py tests/test_release_changelog_agent.py tests/test_codemod_agent.py tests/test_publish_agent.py tests/test_rollback_agent.py tests/test_gate_status_reader.py tests/test_version_calculator.py tests/test_component_inventory_reader.py tests/test_quality_report_parser.py tests/test_ast_pattern_matcher.py tests/test_codemod_template_generator.py tests/test_example_suite_builder.py tests/test_package_json_generator.py tests/test_dependency_resolver.py tests/test_test_result_parser.py tests/test_checkpoint_creator.py tests/test_restore_executor.py tests/test_rollback_reporter.py
  ```
- [x] 2.28 **Git checkpoint:** `git add -A && git commit -m "feat(release): implement Release Crew agents 36-40"`

### 2D. First Publish Agent Integration

- [x] 2.29 Update `src/daf/agents/first_publish.py`:
  - Import `create_rollback_agent`
  - Instantiate Agent 40 at pipeline start and store as `self.rollback_agent` (or pass as parameter to crew delegations)
  - Call `checkpoint_creator.snapshot(phase_name)` before each crew delegation
  - Call `restore_executor.restore(phase_name)` when a crew exhausts its 2-attempt retry budget
- [x] 2.30 Update `tests/test_first_publish_agent.py` — add tests for Agent 40 wiring:
  - `test_rollback_agent_instantiated_at_pipeline_start`
  - `test_snapshot_called_before_each_crew`
  - `test_restore_called_on_exhausted_retry`
- [x] 2.31 Verify updated first_publish tests pass (`pytest tests/test_first_publish_agent.py`)
- [x] 2.32 **Git checkpoint:** `git add -A && git commit -m "feat(release): wire Rollback Agent 40 into First Publish Agent"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `release.py` against design.md — verify model tier constants match design tier assignments (Semver/Haiku, Changelog/Sonnet, Codemod/Haiku, Publish/Haiku, Rollback/Haiku)
- [x] 3.2 Review `dependency_resolver.py` — confirm graceful degradation logic handles all edge cases from tdd.md (FileNotFoundError, OSError, non-zero exit)
- [x] 3.3 Ensure all module docstrings reference the agent number, crew, and phase (e.g. `"""Agent 36 – Semver Agent (Release Crew, Phase 6)."""`)
- [x] 3.4 Review `checkpoint_creator.py` — confirm `checkpoints/` directory is excluded from snapshot copy to prevent infinite recursion
- [x] 3.5 Run full new test suite — confirm all still pass after refactor
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor(release): clean up crew and tool implementation"`

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/ tests/`
- [x] 4.2 Fix all lint errors — zero warnings policy
- [x] 4.3 Run type checker: `pyright src/`
- [x] 4.4 Fix all type errors
- [x] 4.5 Run **full test suite**: `pytest` — verify no regressions in existing tests
- [x] 4.6 Check coverage:
  ```
  pytest \
    --cov=src/daf/crews/release \
    --cov=src/daf/agents/semver \
    --cov=src/daf/agents/release_changelog \
    --cov=src/daf/agents/codemod \
    --cov=src/daf/agents/publish \
    --cov=src/daf/agents/rollback \
    --cov=src/daf/tools/gate_status_reader \
    --cov=src/daf/tools/version_calculator \
    --cov=src/daf/tools/component_inventory_reader \
    --cov=src/daf/tools/quality_report_parser \
    --cov=src/daf/tools/ast_pattern_matcher \
    --cov=src/daf/tools/codemod_template_generator \
    --cov=src/daf/tools/example_suite_builder \
    --cov=src/daf/tools/package_json_generator \
    --cov=src/daf/tools/dependency_resolver \
    --cov=src/daf/tools/test_result_parser \
    --cov=src/daf/tools/checkpoint_creator \
    --cov=src/daf/tools/restore_executor \
    --cov=src/daf/tools/rollback_reporter \
    --cov-report=term-missing
  ```
- [x] 4.7 Confirm ≥80% line coverage on all new modules
- [x] 4.8 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p17-release-crew"` (skip if no changes needed)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 5.4 Push feature branch: `git push origin feat/p17-release-crew`

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p17-release-crew`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p17-release-crew`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p17-release-crew`
- [x] 6.6 Verify clean state: `git branch -a` — feature branch gone, `git status` — clean
