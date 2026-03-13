# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p15-analytics-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `pytest` and `ruff` are available (`pytest --version && ruff --version`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### 1a. Crew factory tests

- [x] 1.1 Create `tests/test_analytics_crew.py` — replace stub assertions with:
  - `test_crew_raises_runtime_error_when_no_spec_files_exist`
  - `test_crew_raises_runtime_error_when_specs_dir_empty`
  - `test_crew_returns_crewai_crew_when_specs_exist`
  - `test_crew_has_five_agents_and_five_tasks`

### 1b. Agent factory tests

- [x] 1.2 Create `tests/test_usage_tracking_agent.py` — Agent 31 (role, model, tools)
- [x] 1.3 Create `tests/test_token_compliance_agent.py` — Agent 32 (role, model, tools)
- [x] 1.4 Create `tests/test_drift_detection_agent.py` — Agent 33 (role, model, tools)
- [x] 1.5 Create `tests/test_pipeline_completeness_agent.py` — Agent 34 (role, model, tools)
- [x] 1.6 Create `tests/test_breakage_correlation_agent.py` — Agent 35 (role, model, tools)

### 1c. Tool tests

- [x] 1.7 Create `tests/test_ast_import_scanner.py` — empty dir, import detection, malformed TSX
- [x] 1.8 Create `tests/test_token_usage_mapper.py` — dead token, all-used, missing tokens dir
- [x] 1.9 Create `tests/test_structural_comparator.py` — drift variants, consistent component, missing doc
- [x] 1.10 Create `tests/test_pipeline_stage_tracker.py` — complete, stuck, empty component list
- [x] 1.11 Create `tests/test_dependency_chain_walker.py` — root-cause, downstream, no failures, missing graph

### 1d. Regression guard

- [x] 1.12 Remove `analytics` row from `CREW_OUTPUT_SPECS` in `tests/test_crew_stubs.py` (analytics graduates to real crew; dedicated test file covers it)
- [x] 1.13 Run `pytest tests/ -x` — confirm all new tests FAIL (ImportError / AttributeError) and no existing tests regress
- [x] 1.14 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p15-analytics-crew"`

## 2. Implementation (TDD — Green Phase)

### 2a. Deterministic tools

- [x] 2.1 Create `src/daf/tools/ast_import_scanner.py`
- [x] 2.2 Create `src/daf/tools/token_usage_mapper.py`
- [x] 2.3 Create `src/daf/tools/structural_comparator.py`
- [x] 2.4 Create `src/daf/tools/drift_reporter.py`
- [x] 2.5 Create `src/daf/tools/doc_patcher.py`
- [x] 2.6 Create `src/daf/tools/pipeline_stage_tracker.py`
- [x] 2.7 Create `src/daf/tools/dependency_chain_walker.py`
- [x] 2.8 Export all seven new tool classes from `src/daf/tools/__init__.py`
- [x] 2.9 Run `pytest tests/test_ast_import_scanner.py tests/test_token_usage_mapper.py tests/test_structural_comparator.py tests/test_pipeline_stage_tracker.py tests/test_dependency_chain_walker.py -x` — verify tool tests pass

### 2b. Agent factories

- [x] 2.10 Create `src/daf/agents/usage_tracking.py` — `create_usage_tracking_agent(model, output_dir)` → `Agent` (Haiku, role "Usage Tracking", tools: `ASTImportScanner`, `TokenUsageMapper`, `DependencyGraphBuilder`)
- [x] 2.11 Create `src/daf/agents/token_compliance_agent.py` — `create_token_compliance_agent(model, output_dir)` → `Agent` (Haiku, role "Token Compliance", tools: `TokenComplianceScannerTool`, `TokenUsageMapper`)

  > **Note:** `TokenComplianceScannerTool` is a thin `BaseTool` wrapper around `compute_token_compliance` from `daf.tools.composition_rule_engine` — do not re-implement scanning logic.

- [x] 2.12 Create `src/daf/agents/drift_detection.py` — `create_drift_detection_agent(model, output_dir)` → `Agent` (Sonnet, role "Drift Detection", tools: `StructuralComparator`, `DriftReporter`, `DocPatcher`)
- [x] 2.13 Create `src/daf/agents/pipeline_completeness.py` — `create_pipeline_completeness_agent(model, output_dir)` → `Agent` (Haiku, role "Pipeline Completeness", tools: `PipelineStageTracker`)
- [x] 2.14 Create `src/daf/agents/breakage_correlation.py` — `create_breakage_correlation_agent(model, output_dir)` → `Agent` (Sonnet, role "Breakage Correlation", tools: `DependencyChainWalker`)
- [x] 2.15 Export five new agent factories from `src/daf/agents/__init__.py`
- [x] 2.16 Run agent factory tests — `pytest tests/test_usage_tracking_agent.py tests/test_token_compliance_agent.py tests/test_drift_detection_agent.py tests/test_pipeline_completeness_agent.py tests/test_breakage_correlation_agent.py -x`

### 2c. Crew factory

- [x] 2.17 Rewrite `src/daf/crews/analytics.py`:
  - Remove `StubCrew` import and stub `_run` function
  - Add pre-flight guard: raise `RuntimeError` if `glob("<output_dir>/specs/*.spec.yaml")` returns empty
  - Instantiate five agents using their factory functions with correct model tiers
  - Define tasks T1–T5 using `crewai.Task` with `context` chaining (T2 context=[T1], T3 context=[T2], etc.)
  - Return `crewai.Crew(agents=[...], tasks=[T1, T2, T3, T4, T5], verbose=False)`
- [x] 2.18 Run crew tests — `pytest tests/test_analytics_crew.py -x`

### 2d. Full test suite (green confirmation)

- [x] 2.19 Run `pytest tests/ -x` — all tests pass (red → green)
- [x] 2.20 **Git checkpoint:** `git add -A && git commit -m "feat(analytics): implement Analytics Crew agents 31-35"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `analytics.py` against design.md — confirm model tiers, task ordering, pre-flight guard
- [x] 3.2 Review tool implementations — eliminate any duplicated scanning logic; confirm `TokenComplianceScannerTool` delegates to `compute_token_compliance`
- [x] 3.3 Check agent `goal` and `backstory` strings are descriptive and non-trivial (align with PRD §4.7 agent descriptions)
- [x] 3.4 Ensure all `reports/` writes happen inside task descriptions (not in `_run` functions)
- [x] 3.5 Verify all new files have `from __future__ import annotations` and `"""Module docstring."""` headers
- [x] 3.6 Run `pytest tests/ -x` — confirm all tests still pass after refactor
- [x] 3.7 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up analytics crew implementation"`

## 4. Integration & Quality

- [x] 4.1 Run `ruff check src/daf/crews/analytics.py src/daf/agents/usage_tracking.py src/daf/agents/token_compliance_agent.py src/daf/agents/drift_detection.py src/daf/agents/pipeline_completeness.py src/daf/agents/breakage_correlation.py src/daf/tools/ast_import_scanner.py src/daf/tools/token_usage_mapper.py src/daf/tools/structural_comparator.py src/daf/tools/drift_reporter.py src/daf/tools/doc_patcher.py src/daf/tools/pipeline_stage_tracker.py src/daf/tools/dependency_chain_walker.py`
- [x] 4.2 Run `ruff check tests/test_analytics_crew.py tests/test_usage_tracking_agent.py tests/test_token_compliance_agent.py tests/test_drift_detection_agent.py tests/test_pipeline_completeness_agent.py tests/test_breakage_correlation_agent.py tests/test_ast_import_scanner.py tests/test_token_usage_mapper.py tests/test_structural_comparator.py tests/test_pipeline_stage_tracker.py tests/test_dependency_chain_walker.py`
- [x] 4.3 Fix all lint errors — zero warnings policy
- [x] 4.4 Run full test suite: `pytest tests/ --tb=short`
- [x] 4.5 Verify no regressions in existing tests (especially `test_crew_stubs.py`, `test_first_publish_agent.py`)
- [x] 4.6 Check coverage — confirm ≥ 80% line coverage per module (all 14 new modules pass; added tests/test_drift_reporter.py, tests/test_doc_patcher.py, tests/test_token_compliance_scanner.py to raise low-coverage tools above threshold)
- [x] 4.7 **Git checkpoint:** `git add -A && git commit -m "feat(analytics): implement Analytics Crew agents 31-35"` (combined with feat commit; coverage test files included)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 5.4 Push feature branch: `git push origin feat/p15-analytics-crew`

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p15-analytics-crew`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p15-analytics-crew`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p15-analytics-crew`
- [x] 6.6 Verify clean state: `git branch -a` (feature branch gone), `git status` (clean)
