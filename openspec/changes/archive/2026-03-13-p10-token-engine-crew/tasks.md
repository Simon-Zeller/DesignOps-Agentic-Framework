# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p10-token-engine-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `pytest` and project dependencies are installed (`pip install -e ".[dev]"` or equivalent)

## 1. Test Scaffolding (TDD — Red Phase)

### 1a. New tool test files

- [x] 1.1 Create `tests/test_dtcg_schema_validator.py` with three failing tests (valid doc, missing `$type`, extra field)
- [x] 1.2 Create `tests/test_naming_linter.py` with three failing tests (clean, abbreviation, wrong casing)
- [x] 1.3 Create `tests/test_reference_graph_walker.py` with two failing tests (simple graph, cross-file ref)
- [x] 1.4 Create `tests/test_circular_ref_detector.py` with two failing tests (clean DAG, direct cycle)
- [x] 1.5 Create `tests/test_orphan_scanner.py` with two failing tests (referenced token, unreferenced token)
- [x] 1.6 Create `tests/test_phantom_ref_scanner.py` with two failing tests (valid refs, missing target)
- [x] 1.7 Create `tests/test_json_diff_engine.py` with three failing tests (initial generation, modified token, removed token)
- [x] 1.8 Create `tests/test_deprecation_tagger.py` with two failing tests (injection, compiled output presence)

### 1b. New agent test files

- [x] 1.9 Create `tests/test_token_ingestion_agent.py` with three failing tests (valid run, missing file, duplicate key)
- [x] 1.10 Create `tests/test_token_validation_agent.py` with five failing tests (clean run, fatal violation, stale rejection cleanup, contrast failure, no colour pairs)
- [x] 1.11 Create `tests/test_token_compilation_agent.py` with four failing tests (all outputs, per-theme files, compiler error, missing theme fallback)
- [x] 1.12 Create `tests/test_token_integrity_agent.py` with three failing tests (clean run, tier-skip fatal, rejection file merge)
- [x] 1.13 Create `tests/test_token_diff_agent.py` with one failing test (diff.json always written)

### 1c. Extended and integration tests

- [x] 1.14 Extend `tests/test_token_compilation_strategy.py` — add two failing tests for `compile_themes()` (verify existing tests still pass)
- [x] 1.15 Create `tests/test_token_engine_crew.py` with two failing integration tests (valid run — all outputs present, invalid run — rejection file written)

### 1d. Red phase confirmation

- [x] 1.16 Run `pytest tests/test_dtcg_schema_validator.py tests/test_naming_linter.py tests/test_reference_graph_walker.py tests/test_circular_ref_detector.py tests/test_orphan_scanner.py tests/test_phantom_ref_scanner.py tests/test_json_diff_engine.py tests/test_deprecation_tagger.py` — confirm all FAIL
- [x] 1.17 Run `pytest tests/test_token_ingestion_agent.py tests/test_token_validation_agent.py tests/test_token_compilation_agent.py tests/test_token_integrity_agent.py tests/test_token_diff_agent.py tests/test_token_engine_crew.py` — confirm all FAIL
- [x] 1.18 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p10-token-engine-crew"`

## 2. Implementation (TDD — Green Phase)

### 2a. New deterministic tools

- [x] 2.1 Implement `src/daf/tools/dtcg_schema_validator.py` — `DTCGSchemaValidator(BaseTool)` with `_run(token_dict)` returning `{fatal, warnings}`; make 1.1 tests pass
- [x] 2.2 Implement `src/daf/tools/naming_linter.py` — `NamingLinter(BaseTool)` with `_run(keys)` returning `{fatal, warnings}` and `BLOCKED_ABBREVIATIONS` constant; make 1.2 tests pass
- [x] 2.3 Implement `src/daf/tools/reference_graph_walker.py` — `ReferenceGraphWalker(BaseTool)` with `_run(base, semantic, component)` returning adjacency-list graph; make 1.3 tests pass
- [x] 2.4 Implement `src/daf/tools/circular_ref_detector.py` — `CircularRefDetector(BaseTool)` with `_run(graph)` using DFS; make 1.4 tests pass
- [x] 2.5 Implement `src/daf/tools/orphan_scanner.py` — `OrphanScanner(BaseTool)` with `_run(graph)` returning orphan paths; make 1.5 tests pass
- [x] 2.6 Implement `src/daf/tools/phantom_ref_scanner.py` — `PhantomRefScanner(BaseTool)` with `_run(merged_namespace, references)` returning phantom entries; make 1.6 tests pass
- [x] 2.7 Implement `src/daf/tools/json_diff_engine.py` — `JsonDiffEngine(BaseTool)` with `_run(current, prior=None)` returning diff dict; make 1.7 tests pass
- [x] 2.8 Implement `src/daf/tools/deprecation_tagger.py` — `DeprecationTagger(BaseTool)` with `_run(token_dict, path, metadata)` injecting `$extensions.com.daf.deprecated`; make 1.8 tests pass
- [x] 2.9 **Green check:** `pytest tests/test_dtcg_schema_validator.py tests/test_naming_linter.py tests/test_reference_graph_walker.py tests/test_circular_ref_detector.py tests/test_orphan_scanner.py tests/test_phantom_ref_scanner.py tests/test_json_diff_engine.py tests/test_deprecation_tagger.py` — all PASS

### 2b. Extend existing tool: `StyleDictionaryCompiler`

- [x] 2.10 Add `compile_themes(token_dir: str, output_dir: str, themes: list[str])` method to `src/daf/tools/style_dictionary_compiler.py` — iterates themes, uses `theme_utils.py` to expand per-theme values, writes `variables-{theme}.css` per theme
- [x] 2.11 **Green check:** `pytest tests/test_token_compilation_strategy.py` — both new tests and all existing tests PASS

### 2c. Five new agent modules

- [x] 2.12 Implement `src/daf/agents/token_ingestion.py` — `create_token_ingestion_agent()` and `create_token_ingestion_task(output_dir, context_tasks=None)`; Agent 7 (Tier 3 Haiku); tools: `WC3DTCGFormatter`; normalises to `tokens/staged/`; raises on missing file or duplicates; make 1.9 tests pass
- [x] 2.13 Implement `src/daf/agents/token_validation.py` — `create_token_validation_agent()` and `create_token_validation_task(output_dir, context_tasks=None)`; Agent 8 (Tier 2 Sonnet); tools: `DTCGSchemaValidator`, `NamingLinter`, `ContrastSafePairer`; writes/deletes `tokens/validation-rejection.json`; make 1.10 tests pass
- [x] 2.14 Implement `src/daf/agents/token_compilation.py` — `create_token_compilation_agent()` and `create_token_compilation_task(output_dir, brand_profile, context_tasks=None)`; Agent 9 (Tier 3 Haiku); tools: `StyleDictionaryCompiler`; invokes `compile()` and `compile_themes()`; make 1.11 tests pass
- [x] 2.15 Implement `src/daf/agents/token_integrity.py` — `create_token_integrity_agent()` and `create_token_integrity_task(output_dir, context_tasks=None)`; Agent 10 (Tier 2 Sonnet); tools: `ReferenceGraphWalker`, `CircularRefDetector`, `OrphanScanner`, `PhantomRefScanner`; appends fatal violations to `tokens/validation-rejection.json`; writes `tokens/integrity-report.json`; make 1.12 tests pass
- [x] 2.16 Implement `src/daf/agents/token_diff.py` — `create_token_diff_agent()` and `create_token_diff_task(output_dir, context_tasks=None)`; Agent 11 (Tier 3 Haiku); tools: `JsonDiffEngine`, `DeprecationTagger`; writes `tokens/diff.json`; make 1.13 tests pass

### 2d. Replace Token Engine Crew stub

- [x] 2.17 Replace `src/daf/crews/token_engine.py` stub with a real `Crew` factory: `create_token_engine_crew(output_dir, brand_profile)` — sequences five tasks T1→T5 using the five new agents; `StubCrew` import removed; make 1.15 integration tests pass
- [x] 2.18 Update `src/daf/agents/__init__.py` to export the five new agent factory functions

### 2e. Green phase confirmation

- [x] 2.19 Run `pytest tests/test_token_ingestion_agent.py tests/test_token_validation_agent.py tests/test_token_compilation_agent.py tests/test_token_integrity_agent.py tests/test_token_diff_agent.py tests/test_token_engine_crew.py` — all PASS
- [x] 2.20 **Git checkpoint:** `git add -A && git commit -m "feat: implement p10-token-engine-crew — agents 7–11, new tools, real crew factory"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review all five agent modules against `design.md` — verify tier assignments, tool bindings, and task descriptions match the design
- [x] 3.2 Extract shared rejection-file read/write/delete helpers into a private utility module `src/daf/tools/_rejection_file.py` if duplication exists across agents 8 and 10
- [x] 3.3 Ensure `BLOCKED_ABBREVIATIONS` in `naming_linter.py` is documented and complete per PRD §4.2 naming guidance
- [x] 3.4 Verify no direct global-token imports in component/semantic tool logic (token-first rule applies to framework code too)
- [x] 3.5 Run all new tests — confirm all still PASS after refactor
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p10-token-engine-crew — shared helpers, naming, docs"`

## 4. Integration & Quality

- [x] 4.1 Run `ruff check src/ tests/` — fix all lint violations
- [x] 4.2 Run `pyright src/` (or `mypy src/`) — fix all type errors; zero warnings policy
- [x] 4.3 Run full test suite: `pytest` — verify zero regressions in existing tests
- [x] 4.4 Check coverage: `pytest --cov=src/daf --cov-report=term-missing` — verify new modules meet ≥ 80% line coverage; new tools should approach 100%
- [x] 4.5 If any new module is below 80%, add missing test cases and iterate (green → refactor loop)
- [x] 4.6 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p10-token-engine-crew"` (skip if no changes)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch; messages follow Conventional Commits
- [x] 5.3 `git fetch origin && git rebase origin/main` — rebase on latest main if needed
- [x] 5.4 Push feature branch: `git push origin feat/p10-token-engine-crew`

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p10-token-engine-crew`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p10-token-engine-crew`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p10-token-engine-crew`
- [x] 6.6 Verify clean state: `git branch -a` — feature branch gone; `git status` — clean
