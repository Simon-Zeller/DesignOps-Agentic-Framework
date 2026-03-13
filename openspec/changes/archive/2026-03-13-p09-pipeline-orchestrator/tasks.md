# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p09-pipeline-orchestrator`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm Python ≥3.11 is active (`python --version`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

- [x] 1.1 Create `tests/test_checkpoint_manager.py` with all `CheckpointManager` test cases from tdd.md:
  - `test_checkpoint_create_writes_snapshot_and_manifest`
  - `test_checkpoint_does_not_include_checkpoints_dir`
  - `test_checkpoint_restore_overwrites_output_dir`
  - `test_checkpoint_restore_raises_on_corrupt`
  - `test_get_last_valid_checkpoint_returns_highest_valid_phase`
  - `test_get_last_valid_checkpoint_returns_none_when_all_corrupt`
  - `test_checkpoint_cleanup_removes_all_snapshots`
  - `test_checkpoint_manager_handles_empty_output_dir`

- [x] 1.2 Create `tests/test_crew_sequencer.py` with all `CrewSequencer` test cases from tdd.md:
  - `test_crew_sequencer_invokes_all_eight_crews_in_order`
  - `test_crew_sequencer_enforces_documentation_before_governance`
  - `test_crew_sequencer_fails_fast_on_missing_input`
  - `test_crew_sequencer_optional_inputs_do_not_block`
  - `test_crew_sequencer_empty_required_input_list_does_not_block`

- [x] 1.3 Create `tests/test_result_aggregator.py` with all `ResultAggregator` test cases from tdd.md:
  - `test_result_aggregator_all_success_writes_summary`
  - `test_result_aggregator_phase56_failure_yields_partial`
  - `test_result_aggregator_phase13_failure_yields_failed`
  - `test_result_aggregator_is_idempotent`
  - `test_result_aggregator_empty_crew_result_list_raises`

- [x] 1.4 Create `tests/test_first_publish_agent.py` with all Agent 6 test cases from tdd.md:
  - `test_first_publish_agent_retries_phase2_on_rejection`
  - `test_first_publish_agent_marks_failed_after_three_retries`
  - `test_first_publish_agent_phases46_crew_retry_bounded_at_two`
  - `test_first_publish_agent_retry_context_accumulates`
  - `test_first_publish_agent_instantiates_rollback_agent_at_start`

- [x] 1.5 Create `tests/test_crew_stubs.py` with stub crew test cases from tdd.md:
  - `test_token_engine_stub_writes_required_outputs`
  - `test_all_crew_stubs_write_minimum_outputs` (parametrized over all 8 stubs)

- [x] 1.6 Add resume and Gate 2 tests to `tests/test_cli_init.py`:
  - `test_cli_resume_from_valid_checkpoint`
  - `test_cli_resume_no_checkpoints_exits_nonzero`
  - `test_cli_gate2_approve_exits_zero`

- [x] 1.7 Run `pytest tests/test_checkpoint_manager.py tests/test_crew_sequencer.py tests/test_result_aggregator.py tests/test_first_publish_agent.py tests/test_crew_stubs.py` — confirm all new tests **FAIL** (ImportError or AttributeError expected; anything but a pass is correct)

- [x] 1.8 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p09-pipeline-orchestrator"`

## 2. Implementation (TDD — Green Phase)

### 2a. CheckpointManager tool

- [x] 2.1 Create `src/daf/tools/checkpoint_manager.py`:
  - `CheckpointCorruptError(Exception)` — raised when manifest validation fails
  - `CheckpointManager(BaseTool)` with methods:
    - `create(output_dir: str, phase: int) -> dict` — snapshot to `.daf-checkpoints/phase-<N>-<ts>/`, update `checkpoints.json`
    - `restore(output_dir: str, phase: int) -> None` — validate manifest then `shutil.copytree`
    - `get_last_valid_checkpoint(output_dir: str) -> dict | None` — iterate manifest in phase order
    - `cleanup(output_dir: str) -> None` — remove `.daf-checkpoints/`
  - Snapshot excludes `.daf-checkpoints/` itself
  - Manifest entry: `{phase, timestamp, path, file_manifest: {rel_path: size_bytes}}`

- [x] 2.2 Run `pytest tests/test_checkpoint_manager.py` — all CheckpointManager tests **PASS**

### 2b. Crew stub modules

- [x] 2.3 Create `src/daf/crews/__init__.py` — re-exports all 8 `create_<crew>_crew` factories

- [x] 2.4 Create `src/daf/crews/token_engine.py`:
  - `create_token_engine_crew(output_dir: str) -> Crew`
  - Stub task writes: `tokens/compiled/variables.css`, `tokens/compiled/variables-light.css`, `tokens/compiled/variables-dark.css`, `tokens/compiled/variables-high-contrast.css`, `tokens/compiled/variables.scss`, `tokens/compiled/tokens.ts`, `tokens/compiled/tokens.json`, `tokens/diff.json`; validates tokens files (overwrites raw with `{"stub": true}`)

- [x] 2.5 Create `src/daf/crews/design_to_code.py`:
  - `create_design_to_code_crew(output_dir: str) -> Crew`
  - Stub task writes: `src/primitives/index.ts`, `src/components/index.ts`, `src/index.ts`, `reports/generation-summary.json`; creates `screenshots/` directory

- [x] 2.6 Create `src/daf/crews/component_factory.py`:
  - `create_component_factory_crew(output_dir: str) -> Crew`
  - Stub task writes: `reports/quality-scorecard.json`, `reports/a11y-audit.json`, `reports/composition-audit.json`

- [x] 2.7 Create `src/daf/crews/documentation.py`:
  - `create_documentation_crew(output_dir: str) -> Crew`
  - Stub task writes: `docs/README.md`, `docs/tokens.md`, `docs/search-index.json`, `docs/decisions/generation-narrative.md`, `docs/changelog.md`

- [x] 2.8 Create `src/daf/crews/governance.py`:
  - `create_governance_crew(output_dir: str) -> Crew`
  - Stub task writes: `governance/ownership.json`, `governance/quality-gates.json`, `governance/deprecation-policy.json`, `governance/workflow.json`, `docs/templates/rfc-template.md`, `tests/tokens.test.ts`, `tests/a11y.test.ts`, `tests/composition.test.ts`, `tests/compliance.test.ts`

- [x] 2.9 Create `src/daf/crews/ai_semantic_layer.py`:
  - `create_ai_semantic_layer_crew(output_dir: str) -> Crew`
  - Stub task writes: `registry/components.json`, `registry/tokens.json`, `registry/composition-rules.json`, `registry/compliance-rules.json`, `.cursorrules`, `copilot-instructions.md`, `ai-context.json`

- [x] 2.10 Create `src/daf/crews/analytics.py`:
  - `create_analytics_crew(output_dir: str) -> Crew`
  - Stub task writes: `reports/token-compliance.json`, `reports/drift-report.json`

- [x] 2.11 Create `src/daf/crews/release.py`:
  - `create_release_crew(output_dir: str) -> Crew`
  - Stub task writes: `package.json` (with `{"stub": true}`), updates `reports/generation-summary.json` with `final_status`; writes `docs/changelog.md` (if not created by docs crew already)

- [x] 2.12 Run `pytest tests/test_crew_stubs.py` — all stub tests **PASS**

### 2c. ResultAggregator tool

- [x] 2.13 Create `src/daf/tools/result_aggregator.py`:
  - `CrewResult` dataclass: `crew, phase, status, retries_used, retries_exhausted, artifacts_written, rejection`
  - `ResultAggregator(BaseTool)` with method `aggregate(crew_results: list[CrewResult], output_dir: str) -> str`
  - Writes `reports/generation-summary.json` with `pipeline.status` logic:
    - `"success"` if all `status` in `{"success", "partial"}`
    - `"partial"` if any Phase 4–6 crew `status == "failed"` but no Phase 1–3 exhaustion
    - `"failed"` if any Phase 1–3 crew has `retries_exhausted=True`

- [x] 2.14 Run `pytest tests/test_result_aggregator.py` — all ResultAggregator tests **PASS**

### 2d. StatusReporter tool

- [x] 2.15 Create `src/daf/tools/status_reporter.py`:
  - `StatusReporter(BaseTool)` with methods: `phase_start(phase, crew)`, `phase_complete(phase, crew, duration_s)`, `retry_triggered(phase, crew, attempt, reason)`, `phase_failed(phase, crew, reason)`
  - All methods write structured lines to stdout: `[DAF] phase=<N> crew=<name> event=<type> ...`

### 2e. CrewSequencer tool

- [x] 2.16 Create `src/daf/tools/crew_sequencer.py`:
  - Phase sequence constant derived from PRD §3.1 (8 entries, with intra-phase ordering for Phases 3 and 4)
  - I/O contract table constant: required input paths per crew, optional input paths per crew (from §3.6)
  - `CrewSequencer(BaseTool)` with method `run_sequence(output_dir: str) -> list[CrewResult]`
  - Before each crew: validate required inputs exist; on failure return `CrewResult(status="failed", reason="missing_required_input: <path>")` and mark all remaining crews as `status="skipped"`
  - After each crew: call `StatusReporter` and `CheckpointManager.create(output_dir, phase)` at each phase boundary (phases: 1 after Bootstrap is assumed done, 2 after Token Engine, 3 after Component Factory, 4 after Governance, 5 after Analytics)
  - `CrewSequencer` does NOT implement retry logic — it returns `CrewResult` with `status="rejected"` and the rejection payload; Agent 6 handles retries

- [x] 2.17 Run `pytest tests/test_crew_sequencer.py` — all CrewSequencer tests **PASS**

### 2f. Agent 40 — Rollback Agent

- [x] 2.18 Create `src/daf/agents/rollback.py`:
  - `create_rollback_agent() -> Agent` — Tier 3 (Haiku), tool: `CheckpointManager`
  - `create_rollback_task(output_dir: str, phase: int, action: Literal["create", "restore"]) -> Task`
  - Exported convenience function: `run_rollback(output_dir: str, phase: int, action: str) -> str`

### 2g. Agent 6 — First Publish Agent

- [x] 2.19 Create `src/daf/agents/first_publish.py`:
  - `create_first_publish_agent() -> Agent` — Tier 2 (Sonnet), tools: `CrewSequencer`, `ResultAggregator`, `StatusReporter`
  - `run_first_publish_agent(output_dir: str, brand_profile_path: str, pipeline_config_path: str) -> dict`
    - Instantiate Rollback Agent (Agent 40) at the start
    - Call `CrewSequencer.run_sequence(output_dir)` to get `crew_results`
    - On `CrewResult(status="rejected")` for Phase 1–3 boundaries:
      - Call `run_rollback(output_dir, phase=<pre_phase>, action="restore")`
      - Re-invoke originating Phase 1 agent task function with accumulated `retry_context`
      - Re-run the rejecting crew (via `CrewSequencer` for just that crew, or direct `Crew.kickoff()`)
      - Loop up to `max_component_retries` from `pipeline_config.retry` (default 3)
    - On Phase 4–6 crew failure: retry the crew up to `max_crew_retries` (default 2)
    - Call `ResultAggregator.aggregate(crew_results, output_dir)` at the end
    - Return the parsed `generation-summary.json` as a dict

- [x] 2.20 Run `pytest tests/test_first_publish_agent.py` — all Agent 6 tests **PASS**

### 2h. CLI integration

- [x] 2.21 Modify `src/daf/cli.py`:
  - After Brand Profile approval at Gate 1 in `_load_profile()` / interview flow: call `run_first_publish_agent(output_dir, brand_profile_path, pipeline_config_path)` where `output_dir` defaults to `./output/<profile-name>/`
  - Add Gate 2 prompt after `run_first_publish_agent()` returns: display `pipeline.status`, component counts, and prompt `[A]pprove / [R]e-run full / [P]hase re-run / [C]omponent re-run`
  - `--resume <output-dir>` flag: call `CheckpointManager.get_last_valid_checkpoint(output_dir)`; if `None`, print error and exit 1; if valid, pass `resume_from_phase=checkpoint.phase + 1` to `run_first_publish_agent()`

- [x] 2.22 Run `pytest tests/test_cli_init.py` — all CLI tests (new and existing) **PASS**

- [x] 2.23 **Git checkpoint:** `git add -A && git commit -m "feat: implement p09-pipeline-orchestrator — Agent 6, Agent 40, crew stubs, CLI wiring"`

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `crew_sequencer.py` — extract the I/O contract table to a named constant `CREW_IO_CONTRACTS` with typed entries; no raw dicts inline
- [x] 3.2 Review `first_publish.py` — ensure retry routing loop does not exceed 40 lines; extract `_run_phase1_retry_loop()` helper if needed
- [x] 3.3 Confirm all stub crew modules follow the same pattern (uniform `create_<crew>_crew` signature and stub task structure); refactor any outliers
- [x] 3.4 Verify all tests still pass after refactor (`pytest tests/test_checkpoint_manager.py tests/test_crew_sequencer.py tests/test_result_aggregator.py tests/test_first_publish_agent.py tests/test_crew_stubs.py tests/test_cli_init.py`)
- [x] 3.5 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p09-pipeline-orchestrator"`

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/ tests/` — zero errors
- [x] 4.2 Run type checker: `pyright src/daf/agents/first_publish.py src/daf/agents/rollback.py src/daf/tools/crew_sequencer.py src/daf/tools/checkpoint_manager.py src/daf/tools/result_aggregator.py src/daf/tools/status_reporter.py src/daf/crews/` — zero errors
- [x] 4.3 Fix all lint and type errors — zero warnings policy
- [x] 4.4 Run full test suite: `pytest --cov=src/daf --cov-report=term-missing` — confirm ≥80% line coverage for new modules
- [x] 4.5 Verify no regressions in existing tests (all green)
- [x] 4.6 Update `scripts/bootstrap.sh` — add a stage that exercises `daf init --resume` against a pre-populated output directory with a valid Phase 1 checkpoint, verifying the resume flag is wired and exits correctly
- [x] 4.7 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p09-pipeline-orchestrator"` (skip if no changes)

## 5. Final Verification & Push

- [x] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [x] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [x] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [x] 5.4 Push feature branch (`git push origin feat/p09-pipeline-orchestrator`)

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p09-pipeline-orchestrator`)
- [x] 6.3 Push main (`git push origin main`)
- [x] 6.4 Delete local feature branch (`git branch -d feat/p09-pipeline-orchestrator`)
- [x] 6.5 Delete remote feature branch (`git push origin --delete feat/p09-pipeline-orchestrator`)
- [x] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
