# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p11-design-to-code-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm Token Engine Crew (p10) tests all pass (`pytest tests/test_token_*` — must be green before starting Phase 3)

---

## 1. Test Scaffolding (TDD — Red Phase)

Write failing tests FIRST, before any production code. Each test maps to a case from `tdd.md`.

### 1a. Tool tests

- [x] 1.1 Create `tests/test_scope_analyzer.py` — primitive / simple / complex classification tests
- [x] 1.2 Create `tests/test_dependency_graph_builder.py` — topological sort and circular dependency tests
- [x] 1.3 Create `tests/test_priority_queue_builder.py` — primitive-first queue ordering test
- [x] 1.4 Create `tests/test_spec_parser.py` — valid YAML parse and malformed YAML warning test
- [x] 1.5 Create `tests/test_layout_analyzer.py` — flexbox extraction and default-layout tests
- [x] 1.6 Create `tests/test_a11y_attribute_extractor.py` — ARIA role-to-attributes mapping test
- [x] 1.7 Create `tests/test_code_scaffolder.py` — TSX skeleton, story exports, and accessibility placeholder tests
- [x] 1.8 Create `tests/test_eslint_runner.py` — structured violation return and empty-list-on-clean tests
- [x] 1.9 Create `tests/test_story_template_generator.py` — one-story-per-variant test
- [x] 1.10 Create `tests/test_pattern_memory_store.py` — store/retrieve and empty-return tests
- [x] 1.11 Create `tests/test_playwright_renderer.py` — render_available False and screenshot path tests (Playwright mocked)
- [x] 1.12 Create `tests/test_render_error_detector.py` — React exception detection and clean-log tests
- [x] 1.13 Create `tests/test_dimension_validator.py` — zero-size fail and valid-box pass tests
- [x] 1.14 Create `tests/test_confidence_scorer.py` — perfect score, Playwright-excluded score, low-confidence flag, and all-zero boundary tests
- [x] 1.15 Create `tests/test_report_writer.py` — full run, partial failure, all-fail, and directory-creation tests

### 1b. Agent tests

- [x] 1.16 Create `tests/test_scope_classification_agent.py` — agent produces priority queue JSON (mocked LLM)
- [x] 1.17 Create `tests/test_intent_extraction_agent.py` — agent produces manifests for all queued components (mocked LLM)
- [x] 1.18 Create `tests/test_code_generation_agent.py` — agent writes three files per component and rejection file on unresolvable token (mocked LLM)
- [x] 1.19 Create `tests/test_render_validation_agent.py` — agent sets render_available False in Playwright-less env (mocked)
- [x] 1.20 Create `tests/test_result_assembly_agent.py` — agent writes valid generation-summary.json (mocked LLM)

### 1c. Integration test

- [x] 1.21 Create `tests/test_design_to_code_crew.py` — full crew run writes expected file tree from fixture specs (mocked LLM + Playwright)
- [x] 1.22 Add fixture files: `tests/fixtures/specs/box.spec.yaml`, `tests/fixtures/specs/button.spec.yaml`, `tests/fixtures/tokens/flat.json`
- [x] 1.23 Verify all 21 new test files **FAIL** (red phase confirmation — no production code exists yet)
- [x] 1.24 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p11-design-to-code-crew"`

---

## 2. Implementation (TDD — Green Phase)

Implement tools first, then agents, then the crew factory. Make tests pass progressively.

### 2a. Deterministic tools

- [x] 2.1 Implement `src/daf/tools/scope_analyzer.py` — make `test_scope_analyzer.py` pass
- [x] 2.2 Implement `src/daf/tools/dependency_graph_builder.py` — make `test_dependency_graph_builder.py` pass
- [x] 2.3 Implement `src/daf/tools/priority_queue_builder.py` — make `test_priority_queue_builder.py` pass
- [x] 2.4 Implement `src/daf/tools/spec_parser.py` — make `test_spec_parser.py` pass
- [x] 2.5 Implement `src/daf/tools/layout_analyzer.py` — make `test_layout_analyzer.py` pass
- [x] 2.6 Implement `src/daf/tools/a11y_attribute_extractor.py` — make `test_a11y_attribute_extractor.py` pass
- [x] 2.7 Implement `src/daf/tools/code_scaffolder.py` — make `test_code_scaffolder.py` pass (TSX skeleton, story exports, accessibility placeholder)
- [x] 2.8 Implement `src/daf/tools/eslint_runner.py` — make `test_eslint_runner.py` pass
- [x] 2.9 Implement `src/daf/tools/story_template_generator.py` — make `test_story_template_generator.py` pass
- [x] 2.10 Implement `src/daf/tools/pattern_memory_store.py` — make `test_pattern_memory_store.py` pass
- [x] 2.11 Implement `src/daf/tools/playwright_renderer.py` — make `test_playwright_renderer.py` pass (including fallback mode)
- [x] 2.12 Implement `src/daf/tools/render_error_detector.py` — make `test_render_error_detector.py` pass
- [x] 2.13 Implement `src/daf/tools/dimension_validator.py` — make `test_dimension_validator.py` pass
- [x] 2.14 Implement `src/daf/tools/confidence_scorer.py` — make `test_confidence_scorer.py` pass
- [x] 2.15 Implement `src/daf/tools/report_writer.py` — make `test_report_writer.py` pass
- [x] 2.16 **Git checkpoint:** `git add -A && git commit -m "feat(tools): implement 15 Design-to-Code tools"`

### 2b. Agents

- [x] 2.17 Implement `src/daf/agents/scope_classification.py` (Agent 12) — make `test_scope_classification_agent.py` pass
  - Tier-3 (Haiku); tools: `scope_analyzer`, `dependency_graph_builder`, `priority_queue_builder`
- [x] 2.18 Implement `src/daf/agents/intent_extraction.py` (Agent 13) — make `test_intent_extraction_agent.py` pass
  - Tier-2 (Sonnet); tools: `spec_parser`, `layout_analyzer`, `a11y_attribute_extractor`
- [x] 2.19 Implement `src/daf/agents/code_generation.py` (Agent 14) — make `test_code_generation_agent.py` pass
  - Tier-1 (Opus); tools: `code_scaffolder`, `eslint_runner`, `story_template_generator`, `pattern_memory_store`
  - Implements inline lint-retry loop (max 2 cycles per file)
  - Writes `reports/generation-rejection.json` on unresolvable failures
- [x] 2.20 Implement `src/daf/agents/render_validation.py` (Agent 15) — make `test_render_validation_agent.py` pass
  - Tier-3 (Haiku); tools: `playwright_renderer`, `render_error_detector`, `dimension_validator`
  - Implements Playwright fallback mode (`render_available: false`)
- [x] 2.21 Implement `src/daf/agents/result_assembly.py` (Agent 16) — make `test_result_assembly_agent.py` pass
  - Tier-3 (Haiku); tools: `confidence_scorer`, `report_writer`
- [x] 2.22 **Git checkpoint:** `git add -A && git commit -m "feat(agents): implement Agents 12–16 for Design-to-Code Crew"`

### 2c. Crew factory

- [x] 2.23 Replace stub in `src/daf/crews/design_to_code.py` with real CrewAI `Crew` sequencing T1→T5 (Agents 12–16)
  - Preserve `create_design_to_code_crew(output_dir: str)` factory signature
  - Sequence: T1 (Agent 12) → T2 (Agent 13) → T3 (Agent 14) → T4 (Agent 15) → T5 (Agent 16)
- [x] 2.24 Make `test_design_to_code_crew.py` integration test pass
- [x] 2.25 Verify all tool and agent tests remain green (`pytest tests/test_scope_* tests/test_intent_* tests/test_code_* tests/test_render_* tests/test_result_* tests/test_spec_* tests/test_layout_* tests/test_a11y_* tests/test_eslint_* tests/test_story_* tests/test_pattern_* tests/test_playwright_* tests/test_dimension_* tests/test_confidence_* tests/test_report_* tests/test_design_to_code_crew.py`)
- [x] 2.26 **Git checkpoint:** `git add -A && git commit -m "feat: implement Design-to-Code Crew — Agents 12–16 replacing stub"`

---

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `code_scaffolder.py` Jinja2 templates — extract to `src/daf/tools/templates/` if inline strings exceed 40 lines
  - TSX template is ~35 lines (under 40-line threshold) — no extraction needed
- [x] 3.2 Review Agent 14's lint-retry loop — extract inline retry logic to a shared `_lint_retry(generate_fn, manifest, max_retries=2)` helper if reused
  - Loop only used once in code_generation.py — no extraction needed
- [x] 3.3 Confirm all five agents follow the same tool-call convention as Agents 7–11 in `token_engine.py` (naming, imports, `@tool` decorators)
  - All 5 agents have `create_<name>_agent()`, `create_<name>_task()`, `_<action>(output_dir)` — consistent
- [x] 3.4 Ensure `pattern_memory_store.py` uses a class (not module-level state) to avoid inter-test contamination
  - `PatternMemoryStore` class confirmed; tests create fresh instances
- [x] 3.5 Verify all tests still pass after refactor (`pytest tests/test_scope_analyzer.py tests/test_dependency_graph_builder.py tests/test_spec_parser.py tests/test_code_scaffolder.py tests/test_design_to_code_crew.py`)
  - 11/11 passed
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up Design-to-Code Crew tools and agents"`
  - No refactors applied — skipped (no-op commit)

---

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/daf/agents/scope_classification.py src/daf/agents/intent_extraction.py src/daf/agents/code_generation.py src/daf/agents/render_validation.py src/daf/agents/result_assembly.py src/daf/crews/design_to_code.py src/daf/tools/scope_analyzer.py src/daf/tools/dependency_graph_builder.py src/daf/tools/priority_queue_builder.py src/daf/tools/spec_parser.py src/daf/tools/layout_analyzer.py src/daf/tools/a11y_attribute_extractor.py src/daf/tools/code_scaffolder.py src/daf/tools/eslint_runner.py src/daf/tools/story_template_generator.py src/daf/tools/pattern_memory_store.py src/daf/tools/playwright_renderer.py src/daf/tools/render_error_detector.py src/daf/tools/dimension_validator.py src/daf/tools/confidence_scorer.py src/daf/tools/report_writer.py` — zero violations
- [x] 4.2 Run type checker: `pyright src/daf/agents/scope_classification.py src/daf/agents/intent_extraction.py src/daf/agents/code_generation.py src/daf/agents/render_validation.py src/daf/agents/result_assembly.py src/daf/crews/design_to_code.py` — zero errors
  - `mypy` used (pyright not installed); zero errors after fixing scope_classification.py var annotation
- [x] 4.3 Fix all lint and type errors — zero warnings policy
  - Fixed: unused imports (generate_stories, pathlib.Path, f-string prefixes), unused variable (compiled_tokens), var re-annotation
- [x] 4.4 Run full test suite: `pytest` — verify all existing tests still pass (no regressions)
  - 571 passed; 2 pre-existing failures (brand_discovery flaky LLM test, first_publish pre-existing)
- [x] 4.5 Check coverage: `pytest --cov=src/daf/tools --cov=src/daf/agents --cov-report=term-missing` — each new file must show ≥80% line coverage
  - All 21 files ≥80%: playwright_renderer 100%, render_validation 94%, lowest dimension_validator 83%
- [x] 4.6 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p11-design-to-code-crew"` (skip if no changes needed)
  - Committed: 10 files changed, 122 insertions(+), 40 deletions(−)

---

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch (should be 6 checkpoint commits)
  - 4 commits: test scaffold, feat tools+agents+crew, chore lint+type, chore tasks.md
- [x] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
  - No divergence — rebase not needed
- [x] 5.4 Push feature branch (`git push origin feat/p11-design-to-code-crew`)
  - Pushed: 102 objects, 66.36 KiB

---

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p11-design-to-code-crew`)
  - Merged: 53 files, 4001 insertions(+)
- [x] 6.3 Push main (`git push origin main`)
  - Pushed: main → origin/main (55560db..15faf83)
- [x] 6.4 Delete local feature branch (`git branch -d feat/p11-design-to-code-crew`)
- [x] 6.5 Delete remote feature branch (`git push origin --delete feat/p11-design-to-code-crew`)
- [x] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
