# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

## 0. Pre-flight

- [ ] 0.1 Create feature branch: `feat/p18-retry-rollback-checkpoints`
- [ ] 0.2 Verify clean working tree (`git status`)
- [ ] 0.3 Confirm `pytest` passes on current main before any changes (`uv run pytest tests/ -x -q`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

### PRE-CREW-CHECKPOINT tests (`tests/test_first_publish_agent.py`)

- [ ] 1.1 Add `test_run_simple_crew_creates_checkpoint_before_kickoff`: assert `mock_cm.create` is called once with `phase=2` before crew `kickoff()` when `_run_simple_crew("design_to_code", ...)` is invoked
- [ ] 1.2 Add `test_run_simple_crew_still_calls_kickoff_after_checkpoint`: assert crew `kickoff()` is called regardless of checkpoint creation succeeding
- [ ] 1.3 Add `test_run_first_publish_passes_cm_and_phase_to_simple_crew`: assert `cm.create` is called for Design-to-Code AND Component Factory crews (in addition to existing phase-boundary calls) within `run_first_publish_agent`

### PRE-RETRY-RESTORE tests (`tests/test_first_publish_agent.py`)

- [ ] 1.4 Add `test_run_with_retry_creates_checkpoint_on_first_attempt`: assert `cm.create(phase=4)` is called once on attempt 1 of a Phase 4 crew
- [ ] 1.5 Add `test_run_with_retry_restores_checkpoint_before_second_attempt`: assert `cm.restore(output_dir, phase=4)` is called exactly once when attempt 1 fails and attempt 2 succeeds
- [ ] 1.6 Add `test_run_with_retry_calls_cascade_invalidate_after_restore`: assert `_cascade_invalidate` is called with `(output_dir, 4)` after restore and before retry kickoff
- [ ] 1.7 Add `test_run_with_retry_no_restore_on_first_attempt_success`: assert `cm.restore` is NOT called when attempt 1 succeeds
- [ ] 1.8 Add `test_run_with_retry_restore_count_matches_retry_count`: assert `cm.restore` is called exactly once when `max_retries=2` and all attempts fail

### CASCADE-INVALIDATION tests (`tests/test_first_publish_agent.py`)

- [ ] 1.9 Add `test_cascade_invalidate_removes_phase_gt_n_dirs`: create Phase 1+ dirs in `tmp_path`; call `_cascade_invalidate(tmp_path, 0)`; assert Phase 1+ dirs absent
- [ ] 1.10 Add `test_cascade_invalidate_preserves_earlier_phase_artifacts`: assert Phase 1–3 dirs survive when `_cascade_invalidate(tmp_path, 3)` is called
- [ ] 1.11 Add `test_cascade_invalidate_silently_skips_missing_dirs`: call `_cascade_invalidate` on empty `tmp_path`; assert no exception raised
- [ ] 1.12 Add `test_cascade_invalidate_does_not_remove_checkpoint_dir`: assert `.daf-checkpoints/` survives `_cascade_invalidate(tmp_path, 0)`
- [ ] 1.13 Add `test_run_simple_crew_checkpoint_phase_uses_crew_phase_map` (edge case): verify the phase value passed to `cm.create` is sourced from `_CREW_PHASE_MAP`, not a hardcoded literal
- [ ] 1.14 Add `test_cascade_invalidate_is_idempotent` (edge case): call `_cascade_invalidate` twice; assert no error and target dirs remain absent

### RESUME-RESTORE tests (`tests/test_cli_init.py`)

- [ ] 1.15 Add `test_cli_resume_calls_restore_before_run_first_publish`: mock `get_last_valid_checkpoint` returning `{"phase": 3, ...}`; assert `cm.restore` is called with `phase=3` before `run_first_publish_agent(start_phase=4)`
- [ ] 1.16 Add `test_cli_resume_exits_with_error_on_corrupt_checkpoint`: mock `cm.restore` raising `CheckpointCorruptError`; assert CLI exits non-zero with an error message
- [ ] 1.17 Add `test_cli_resume_no_restore_when_no_checkpoints`: mock `get_last_valid_checkpoint` returning `None`; assert `cm.restore` is NOT called and output contains "No valid checkpoints found"

- [ ] 1.18 Verify ALL 17 new tests **FAIL** (red phase confirmation): `uv run pytest tests/test_first_publish_agent.py tests/test_cli_init.py -x -q 2>&1 | grep -E "FAILED|PASSED|ERROR"`
- [ ] 1.19 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for p18-retry-rollback-checkpoints"`

## 2. Implementation (TDD — Green Phase)

### 2.A — `_CREW_PHASE_MAP` and `_PHASE_ARTIFACT_DIRS` constants

- [ ] 2.1 Add `_CREW_PHASE_MAP: dict[str, int]` to `src/daf/agents/first_publish.py` mapping each crew name to its canonical phase integer (e.g., `"token_engine": 1`, `"design_to_code": 2`, `"component_factory": 2`, `"documentation": 4`, `"governance": 4`, `"ai_semantic_layer": 5`, `"analytics": 5`, `"release": 6`)
- [ ] 2.2 Add `_PHASE_ARTIFACT_DIRS: dict[int, list[str]]` mapping phase numbers to the output subdirectory names they produce (e.g., `{1: ["tokens"], 2: ["src/components"], 3: ["src/components", "src/primitives"], 4: ["docs"], 5: ["reports/analytics", "reports/semantic"], 6: ["package.json", "src/index.ts"]}`) — use path-relative strings matching the I/O contracts in §3.6

### 2.B — `_cascade_invalidate` helper

- [ ] 2.3 Add `def _cascade_invalidate(output_dir: str, from_phase: int) -> None` to `src/daf/agents/first_publish.py`: iterate `_PHASE_ARTIFACT_DIRS` for all phases > `from_phase`; for each listed path, remove the corresponding item in `output_dir` (using `shutil.rmtree` for directories, `Path.unlink` for files); skip if not present; never touch `.daf-checkpoints/`

### 2.C — `_run_simple_crew` pre-run checkpoint

- [ ] 2.4 Add `cm: CheckpointManager` and `phase: int` parameters to `_run_simple_crew`
- [ ] 2.5 Insert `cm.create(output_dir=output_dir, phase=phase)` as the first line inside `_run_simple_crew`, before `crew.kickoff()`
- [ ] 2.6 Update both `_run_simple_crew` call sites in `run_first_publish_agent` to pass `cm=cm` and `phase=_CREW_PHASE_MAP[crew_name]`

### 2.D — `_run_with_retry` pre-retry restore

- [ ] 2.7 Add `cm: CheckpointManager` and `phase: int` parameters to `_run_with_retry`
- [ ] 2.8 On attempt 1 (`attempt == 1`), call `cm.create(output_dir=output_dir, phase=phase)` before `crew.kickoff()`
- [ ] 2.9 On attempt > 1 (retry path), call `cm.restore(output_dir=output_dir, phase=phase)` then `_cascade_invalidate(output_dir, phase)` before `crew.kickoff()`
- [ ] 2.10 Update all `_run_with_retry` call sites in `run_first_publish_agent` to pass `cm=cm` and `phase=_CREW_PHASE_MAP[crew_name]`

### 2.E — `_run_phase13_crew` cascade after restore

- [ ] 2.11 In `_run_phase13_crew`, add `_cascade_invalidate(output_dir, pre_checkpoint_phase)` immediately after `cm.restore(output_dir=output_dir, phase=pre_checkpoint_phase)` (the existing restore call in the retry branch)

### 2.F — CLI `--resume` path

- [ ] 2.12 In `src/daf/cli.py`, import `CheckpointCorruptError` from `daf.tools.checkpoint_manager`
- [ ] 2.13 In the `--resume` branch, after `get_last_valid_checkpoint` returns a valid entry, add:
  ```python
  try:
      CheckpointManager().restore(output_dir=resume, phase=checkpoint["phase"])
  except CheckpointCorruptError as exc:
      typer.echo(f"Checkpoint is corrupt and cannot be restored: {exc}. Please restart from Phase 1.")
      raise typer.Exit(code=1)
  ```
  before the `run_first_publish_agent(resume, start_phase=checkpoint["phase"] + 1)` call

- [ ] 2.14 Verify all 17 new tests **PASS**: `uv run pytest tests/test_first_publish_agent.py tests/test_cli_init.py -x -q`
- [ ] 2.15 **Git checkpoint:** `git add -A && git commit -m "feat: add pre-crew checkpoints, pre-retry restore, cascade invalidation, and resume restore (p18)"`

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Review `_PHASE_ARTIFACT_DIRS` paths against §3.6 Crew I/O contracts — confirm every path is accurate and complete
- [ ] 3.2 Ensure `_cascade_invalidate` docstring clearly explains the cascade-forward invariant and references §3.4
- [ ] 3.3 Verify no magic phase-number literals remain in `first_publish.py` outside `_CREW_PHASE_MAP` and `_PHASE_ARTIFACT_DIRS`
- [ ] 3.4 Confirm all tests still pass after any refactor edits
- [ ] 3.5 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up p18 cascade invalidation and phase mapping"`

## 4. Integration & Quality

- [ ] 4.1 Run linter: `uv run ruff check src/daf/agents/first_publish.py src/daf/cli.py`
- [ ] 4.2 Run type checker: `uv run pyright src/daf/agents/first_publish.py src/daf/cli.py`
- [ ] 4.3 Fix all lint and type errors — zero warnings policy
- [ ] 4.4 Run full test suite: `uv run pytest tests/ -q`
- [ ] 4.5 Verify no regressions in existing tests (all pre-existing tests pass)
- [ ] 4.6 Check coverage on modified files: `uv run pytest tests/test_first_publish_agent.py tests/test_cli_init.py --cov=daf.agents.first_publish --cov=daf.cli --cov-report=term-missing`; confirm ≥ 80% line coverage
- [ ] 4.7 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for p18-retry-rollback-checkpoints"` (skip if no changes)

## 5. Final Verification & Push

- [ ] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [ ] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [ ] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [ ] 5.4 Push feature branch: `git push origin feat/p18-retry-rollback-checkpoints`

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p18-retry-rollback-checkpoints`
- [ ] 6.3 Push main: `git push origin main`
- [ ] 6.4 Delete local feature branch: `git branch -d feat/p18-retry-rollback-checkpoints`
- [ ] 6.5 Delete remote feature branch: `git push origin --delete feat/p18-retry-rollback-checkpoints`
- [ ] 6.6 Verify clean state: `git branch -a` — feature branch gone; `git status` — clean
