# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p12-component-factory-crew`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm Python dependencies are current (`pip install -e ".[dev]"` or equivalent)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write ALL failing tests first, before any production code.
     Follow the test inventory from tdd.md exactly. -->

**Test fixtures first:**
- [x] 1.1 Create `tests/fixtures/specs/button.spec.yaml` — valid Button spec with all required fields, resolved token refs, valid states (reuse or extend p11 fixture)
- [x] 1.2 Create `tests/fixtures/specs/badge-unresolved-token.spec.yaml` — spec referencing `color.status.info` (not in compiled tokens)
- [x] 1.3 Create `tests/fixtures/specs/invalid-state-machine.spec.yaml` — spec with terminal state having an outgoing transition
- [x] 1.4 Create `tests/fixtures/tsx/Button.tsx` — clean TSX using only Pressable + Text primitives (reuse or extend p11 fixture)
- [x] 1.5 Create `tests/fixtures/tsx/Modal.tsx` — modal TSX missing `role="dialog"`, focus trap, and Escape handler
- [x] 1.6 Create `tests/fixtures/tsx/NonPrimitive.tsx` — TSX importing `@radix-ui/react-dialog`
- [x] 1.7 Create `tests/fixtures/tsx/Button.test.tsx` — test file containing `// @accessibility-placeholder` at end
- [x] 1.8 Create `tests/fixtures/coverage/lcov.json` — Vitest coverage fixture for `Button.tsx` at 95% line coverage
- [x] 1.9 Create `tests/fixtures/brand-profile-aaa.json` — brand profile with `a11y_level: "AAA"` (complement the existing AA fixture if present)

**Tool tests:**
- [x] 1.10 Create `tests/test_json_schema_validator.py` — tests for valid spec pass, missing field returns error
- [x] 1.11 Create `tests/test_token_ref_checker.py` — tests for resolved refs, unresolved ref detected, empty tokens dict
- [x] 1.12 Create `tests/test_state_machine_validator.py` — tests for valid graph, terminal-to-non-terminal, unreachable state
- [x] 1.13 Create `tests/test_primitive_registry.py` — tests for known primitive, unknown element, full registry list
- [x] 1.14 Create `tests/test_composition_rule_engine.py` — tests for clean TSX, non-primitive import, token compliance ratio
- [x] 1.15 Create `tests/test_nesting_validator.py` — tests for Pressable-in-Pressable, depth > 5 warning, valid nesting
- [x] 1.16 Create `tests/test_aria_generator.py` — tests for button→aria-disabled, dialog→role+aria-modal, status→aria-live
- [x] 1.17 Create `tests/test_keyboard_nav_scaffolder.py` — tests for dialog Escape handler, listbox arrow-key handlers
- [x] 1.18 Create `tests/test_focus_trap_validator.py` — tests for missing trap in dialog, valid trap passes, non-dialog skipped
- [x] 1.19 Create `tests/test_coverage_reporter.py` — tests for coverage from fixture, absent file returns None, missing component returns None
- [x] 1.20 Create `tests/test_score_calculator.py` — tests for correct composite, missing coverage defaults, determinism, all-zero boundary
- [x] 1.21 Create `tests/test_threshold_gate.py` — tests for ≥70 passes, <70 fails, bulk pass/fail split

**Agent tests:**
- [x] 1.22 Create `tests/test_spec_validation_agent.py` — mocked Agent 17: valid spec produces no rejection; unresolved token writes rejection
- [x] 1.23 Create `tests/test_composition_agent.py` — mocked Agent 18: clean TSX records valid; non-primitive import writes rejection
- [x] 1.24 Create `tests/test_accessibility_agent.py` — mocked Agent 19: patches aria-disabled; appends a11y block; restores source after 3 failed tsc calls
- [x] 1.25 Create `tests/test_quality_scoring_agent.py` — mocked Agent 20: correct composite written; gate-failed entry + rejection for <70 score

**Integration test:**
- [x] 1.26 Create `tests/test_component_factory_crew.py` — integration test: Button fixture in, all three reports written, `gate: "passed"`, checkpoint written; LLM calls mocked

**Verify red phase:**
- [x] 1.27 Run `pytest tests/test_json_schema_validator.py tests/test_token_ref_checker.py tests/test_state_machine_validator.py tests/test_primitive_registry.py tests/test_composition_rule_engine.py tests/test_nesting_validator.py tests/test_aria_generator.py tests/test_keyboard_nav_scaffolder.py tests/test_focus_trap_validator.py tests/test_coverage_reporter.py tests/test_score_calculator.py tests/test_threshold_gate.py` — all new tool tests FAIL (ImportError expected)
- [x] 1.28 Run `pytest tests/test_spec_validation_agent.py tests/test_composition_agent.py tests/test_accessibility_agent.py tests/test_quality_scoring_agent.py tests/test_component_factory_crew.py` — all new agent/integration tests FAIL
- [x] 1.29 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p12-component-factory-crew"`

## 2. Implementation (TDD — Green Phase)

**Tools — implement to make tool tests pass:**
- [x] 2.1 Implement `src/daf/tools/primitive_registry.py` — canonical list of 9 base primitives and 11 exports; `is_primitive(name)` and `get_all_primitives()` functions
- [x] 2.2 Implement `src/daf/tools/json_schema_validator.py` — `validate_spec_schema(spec_dict, schema)` using Python `jsonschema` library; returns `{valid, errors}`
- [x] 2.3 Implement `src/daf/tools/token_ref_checker.py` — `check_token_refs(spec_tokens, compiled_tokens)` that flattens compiled token keys and checks against spec refs; returns `{unresolved, all_resolved}`
- [x] 2.4 Implement `src/daf/tools/state_machine_validator.py` — `validate_state_machine(states)` using graph reachability analysis; detects terminal-with-outgoing-transitions and unreachable states
- [x] 2.5 Implement `src/daf/tools/composition_rule_engine.py` — `check_composition(tsx_source, registry)` using import-line regex + JSX element scan; `compute_token_compliance(tsx_source)` counting token var references vs hardcoded values
- [x] 2.6 Implement `src/daf/tools/nesting_validator.py` — `validate_nesting(tsx_source)` detecting forbidden nesting patterns via JSX string scanning and computing nesting depth
- [x] 2.7 Implement `src/daf/tools/aria_generator.py` — `generate_aria_patches(spec, component_type)` mapping component type + states to ARIA attribute patch instructions using a rule table
- [x] 2.8 Implement `src/daf/tools/keyboard_nav_scaffolder.py` — `scaffold_keyboard_handlers(component_type, callbacks)` generating onKeyDown handler stubs for ARIA role patterns (dialog, listbox, tabs, menu)
- [x] 2.9 Implement `src/daf/tools/focus_trap_validator.py` — `validate_focus_trap(tsx_source, component_type)` checking for `useEffect` focus management, Tab cycling patterns, and `not_applicable` pass-through for non-dialog types
- [x] 2.10 Implement `src/daf/tools/coverage_reporter.py` — `get_coverage(component_file, coverage_path)` reading Vitest LCOV/JSON output; returns float 0.0–1.0 or `None`
- [x] 2.11 Implement `src/daf/tools/score_calculator.py` — `calculate_score(sub_scores)` computing weighted composite; handles `None` coverage with `coverage_unavailable: True` flag
- [x] 2.12 Implement `src/daf/tools/threshold_gate.py` — `apply_gate(score, threshold)` and `gate_components(scores, threshold)` returning pass/fail verdicts
- [x] 2.13 Run tool tests — all 12 tool test files PASS: `pytest tests/test_json_schema_validator.py tests/test_token_ref_checker.py tests/test_state_machine_validator.py tests/test_primitive_registry.py tests/test_composition_rule_engine.py tests/test_nesting_validator.py tests/test_aria_generator.py tests/test_keyboard_nav_scaffolder.py tests/test_focus_trap_validator.py tests/test_coverage_reporter.py tests/test_score_calculator.py tests/test_threshold_gate.py`

**Agents — implement to make agent tests pass:**
- [x] 2.14 Implement `src/daf/agents/spec_validation.py` — Agent 17: Spec Validation Agent (Tier-3 Haiku); tools: `json_schema_validator`, `token_ref_checker`, `state_machine_validator`; writes rejection payloads via `_rejection_file.py` for validation failures
- [x] 2.15 Implement `src/daf/agents/composition.py` — Agent 18: Composition Agent (Tier-3 Haiku); tools: `composition_rule_engine`, `primitive_registry`, `nesting_validator`; writes composition audit entries and rejection payloads for violations
- [x] 2.16 Implement `src/daf/agents/accessibility.py` — Agent 19: Accessibility Agent (Tier-2 Sonnet); tools: `aria_generator`, `keyboard_nav_scaffolder`, `focus_trap_validator`, `a11y_attribute_extractor` (existing); reads `brand-profile.json` for AA/AAA calibration; patches TSX in place; appends a11y blocks to `.test.tsx`; runs post-patch re-validation (tsc subprocess + playwright_renderer); self-correction loop bounded to 3 attempts; restores pre-patch backup on persistent failure
- [x] 2.17 Implement `src/daf/agents/quality_scoring.py` — Agent 20: Quality Scoring Agent (Tier-3 Haiku); tools: `coverage_reporter`, `score_calculator`, `threshold_gate`, `report_writer`; reads Agent 17/18/19 audit outputs; writes `quality-scorecard.json`, `a11y-audit.json`, `composition-audit.json`; writes checkpoint file
- [x] 2.18 Run agent tests — all four agent test files PASS: `pytest tests/test_spec_validation_agent.py tests/test_composition_agent.py tests/test_accessibility_agent.py tests/test_quality_scoring_agent.py`

**Crew factory — replace stub:**
- [x] 2.19 Replace stub in `src/daf/crews/component_factory.py` with real CrewAI `Crew` sequencing Agents 17→18→19→20 across tasks T1→T5; preserve `create_component_factory_crew(output_dir: str) -> Crew` signature
- [x] 2.20 Run integration test — `pytest tests/test_component_factory_crew.py` PASSES

**Verify full green phase:**
- [x] 2.21 Run all new tests: `pytest tests/test_json_schema_validator.py tests/test_token_ref_checker.py tests/test_state_machine_validator.py tests/test_primitive_registry.py tests/test_composition_rule_engine.py tests/test_nesting_validator.py tests/test_aria_generator.py tests/test_keyboard_nav_scaffolder.py tests/test_focus_trap_validator.py tests/test_coverage_reporter.py tests/test_score_calculator.py tests/test_threshold_gate.py tests/test_spec_validation_agent.py tests/test_composition_agent.py tests/test_accessibility_agent.py tests/test_quality_scoring_agent.py tests/test_component_factory_crew.py` — ALL PASS
- [x] 2.22 **Git checkpoint:** `git add -A && git commit -m "feat: implement p12-component-factory-crew — 4 agents, 12 tools, crew factory"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `composition_rule_engine.py` and `nesting_validator.py` — extract shared TSX source scanning logic into a shared helper if duplication exists; ensure `ts-node` fallback path is clearly separated from the fast heuristic path
- [x] 3.2 Review `accessibility.py` agent — confirm the pre-patch backup/restore logic is clean and the 3-attempt self-correction loop is readable
- [x] 3.3 Review `quality_scoring.py` agent — confirm all three report files (`quality-scorecard.json`, `a11y-audit.json`, `composition-audit.json`) share consistent schema and are written atomically
- [x] 3.4 Confirm all new modules are exported from `src/daf/tools/__init__.py` and `src/daf/agents/__init__.py`
- [x] 3.5 Verify all tests still PASS after refactor: `pytest tests/test_json_schema_validator.py tests/test_token_ref_checker.py tests/test_state_machine_validator.py tests/test_primitive_registry.py tests/test_composition_rule_engine.py tests/test_nesting_validator.py tests/test_aria_generator.py tests/test_keyboard_nav_scaffolder.py tests/test_focus_trap_validator.py tests/test_coverage_reporter.py tests/test_score_calculator.py tests/test_threshold_gate.py tests/test_spec_validation_agent.py tests/test_composition_agent.py tests/test_accessibility_agent.py tests/test_quality_scoring_agent.py tests/test_component_factory_crew.py`
- [x] 3.6 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p12-component-factory-crew implementation"`

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/daf/tools/json_schema_validator.py src/daf/tools/token_ref_checker.py src/daf/tools/state_machine_validator.py src/daf/tools/primitive_registry.py src/daf/tools/composition_rule_engine.py src/daf/tools/nesting_validator.py src/daf/tools/aria_generator.py src/daf/tools/keyboard_nav_scaffolder.py src/daf/tools/focus_trap_validator.py src/daf/tools/coverage_reporter.py src/daf/tools/score_calculator.py src/daf/tools/threshold_gate.py src/daf/agents/spec_validation.py src/daf/agents/composition.py src/daf/agents/accessibility.py src/daf/agents/quality_scoring.py src/daf/crews/component_factory.py`
- [x] 4.2 Run type checker: `pyright src/daf/tools/ src/daf/agents/ src/daf/crews/component_factory.py` (or `mypy` as configured)
- [x] 4.3 Fix all lint and type errors — zero warnings policy
- [x] 4.4 Run full test suite: `pytest tests/` — verify ALL tests pass (new + existing)
- [x] 4.5 Verify no regressions in p01–p11 tests: `pytest tests/ -k "not test_component_factory_crew"` produces same pass count as before this change
- [x] 4.6 Check test coverage: `pytest tests/test_json_schema_validator.py tests/test_token_ref_checker.py tests/test_state_machine_validator.py tests/test_primitive_registry.py tests/test_composition_rule_engine.py tests/test_nesting_validator.py tests/test_aria_generator.py tests/test_keyboard_nav_scaffolder.py tests/test_focus_trap_validator.py tests/test_coverage_reporter.py tests/test_score_calculator.py tests/test_threshold_gate.py --cov=src/daf/tools --cov-report=term-missing` — confirm ≥80% line coverage per new tool file
- [x] 4.7 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p12-component-factory-crew"` (skip if no changes needed)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch (expected: test scaffold, feat implement, refactor, chore lint fix)
- [x] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 5.4 Push feature branch: `git push origin feat/p12-component-factory-crew`

## 6. Delivery

- [x] 6.1 All tasks 0–5 above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p12-component-factory-crew`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p12-component-factory-crew`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p12-component-factory-crew`
- [x] 6.6 Verify clean state: `git branch -a` — feature branch gone; `git status` — clean
