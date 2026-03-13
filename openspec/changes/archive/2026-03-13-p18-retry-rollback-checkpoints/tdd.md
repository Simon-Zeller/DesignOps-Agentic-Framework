# TDD Plan: p18-retry-rollback-checkpoints

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests are **unit tests** using `pytest` with `tmp_path` for isolated filesystem state and `unittest.mock` (`MagicMock`, `patch`) for all LLM/CrewAI boundary stubbing. No integration or e2e tests — the checkpoint/restore logic is deterministic and fully testable in isolation.

- Framework: `pytest` (existing project standard)
- Fixtures: `tmp_path` (filesystem), `MagicMock` (CrewAI stubs)
- Coverage target: ≥ 80% line coverage on modified files per PRD quality gate
- Red-green rule: each test must fail before implementation, pass after

Existing tests in `tests/test_first_publish_agent.py` and `tests/test_cli_init.py` are extended; no new test files are created.

---

## Test Cases

### PRE-CREW-CHECKPOINT — Checkpoint before every crew run

#### Test: `test_run_simple_crew_creates_checkpoint_before_kickoff`

- **Maps to:** Requirement "PRE-CREW-CHECKPOINT" → Scenario "Design-to-Code crew happy path"
- **Type:** unit
- **Given:** `tmp_path` contains a `brand-profile.json` file; a mock `CheckpointManager` instance is injected; a mock crew factory is set up to return a `CrewResult(status="success")`
- **When:** `_run_simple_crew("design_to_code", factory, str(tmp_path), mock_cm, phase=2, reporter=mock_reporter)` is called
- **Then:** `mock_cm.create.assert_called_once_with(output_dir=str(tmp_path), phase=2)`; `mock_cm.create` was called before the crew factory's `kickoff()`
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_simple_crew_still_calls_kickoff_after_checkpoint`

- **Maps to:** Requirement "PRE-CREW-CHECKPOINT" → Scenario "Crew kickoff still called after checkpoint creation"
- **Type:** unit
- **Given:** `mock_cm.create` succeeds without error; mock crew factory returns success
- **When:** `_run_simple_crew(...)` is called
- **Then:** `mock_crew.kickoff.assert_called_once()` — kickoff is executed regardless of checkpoint creation
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_first_publish_passes_cm_and_phase_to_simple_crew`

- **Maps to:** Requirement "PRE-CREW-CHECKPOINT" → Scenario "Design-to-Code crew happy path" and "Component Factory crew happy path"
- **Type:** unit
- **Given:** Full `run_first_publish_agent` test harness (existing pattern); mock `CheckpointManager.create` tracked via spy
- **When:** `run_first_publish_agent(str(tmp_path))` is called
- **Then:** `cm.create` is called with a phase argument for Design-to-Code AND a phase argument for Component Factory (two calls in addition to the existing boundary checkpoints); call order — `create` before `kickoff` for each crew
- **File:** `tests/test_first_publish_agent.py`

---

### PRE-RETRY-RESTORE — Restore checkpoint before each retry attempt (Phases 4–6)

#### Test: `test_run_with_retry_creates_checkpoint_on_first_attempt`

- **Maps to:** Requirement "PRE-RETRY-RESTORE" → Scenario "Phase 4 Documentation crew fails once and succeeds on retry"
- **Type:** unit
- **Given:** Mock crew factory returns failure on attempt 1, success on attempt 2; mock `CheckpointManager` injected
- **When:** `_run_with_retry("documentation", factory, str(tmp_path), max_retries=2, cm=mock_cm, phase=4, reporter=mock_reporter)` is called
- **Then:** `mock_cm.create.call_count == 1`; the create call uses `phase=4`
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_with_retry_restores_checkpoint_before_second_attempt`

- **Maps to:** Requirement "PRE-RETRY-RESTORE" → Scenario "Phase 4 Documentation crew fails once and succeeds on retry"
- **Type:** unit
- **Given:** Mock crew factory fails on attempt 1, succeeds on attempt 2
- **When:** `_run_with_retry(...)` is called
- **Then:** `mock_cm.restore.assert_called_once_with(output_dir=str(tmp_path), phase=4)` — restore is called exactly once, before attempt 2
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_with_retry_calls_cascade_invalidate_after_restore`

- **Maps to:** Requirement "PRE-RETRY-RESTORE" → Scenario "Phase 4 Documentation crew fails once and succeeds on retry"
- **Type:** unit
- **Given:** Mock crew fails on attempt 1 then succeeds; `_cascade_invalidate` patched as a MagicMock
- **When:** `_run_with_retry(...)` is called
- **Then:** `mock_cascade.assert_called_once_with(str(tmp_path), 4)` — cascade invalidation runs after restore and before retry kickoff
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_with_retry_no_restore_on_first_attempt_success`

- **Maps to:** Requirement "PRE-RETRY-RESTORE" → Scenario "Phase 4 crew succeeds on first attempt"
- **Type:** unit
- **Given:** Mock crew factory returns success on attempt 1
- **When:** `_run_with_retry(...)` is called
- **Then:** `mock_cm.restore.assert_not_called()`; result has `status="success"` and `retries_used=0`
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_run_with_retry_restore_count_matches_retry_count`

- **Maps to:** Requirement "PRE-RETRY-RESTORE" → Scenario "Phase 5 crew exhausts all retries"
- **Type:** unit
- **Given:** Mock crew always fails; `max_retries=2`
- **When:** `_run_with_retry(...)` exhausts retries
- **Then:** `mock_cm.restore.call_count == 1` (restore called once — before attempt 2 only); result has `retries_exhausted=True`
- **File:** `tests/test_first_publish_agent.py`

---

### CASCADE-INVALIDATION — Forward cascade after rollback

#### Test: `test_cascade_invalidate_removes_phase_gt_n_dirs`

- **Maps to:** Requirement "CASCADE-INVALIDATION" → Scenario "Rollback to Phase 0 in cross-phase retry"
- **Type:** unit
- **Given:** `tmp_path` contains directories matching Phase 1+ artifact paths per `_PHASE_ARTIFACT_DIRS` (e.g., `tokens/`, `src/`, `docs/`)
- **When:** `_cascade_invalidate(str(tmp_path), 0)` is called
- **Then:** All Phase 1+ directories listed in `_PHASE_ARTIFACT_DIRS` are removed from `tmp_path`; `.daf-checkpoints/` is NOT removed
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_cascade_invalidate_preserves_earlier_phase_artifacts`

- **Maps to:** Requirement "CASCADE-INVALIDATION" → Scenario "Phase 4 retry cascade"
- **Type:** unit
- **Given:** `tmp_path` contains `tokens/` (Phase 1), `src/` (Phase 2-3), and `docs/` (Phase 4+)
- **When:** `_cascade_invalidate(str(tmp_path), 3)` is called
- **Then:** `tokens/` and `src/` remain; `docs/` (Phase 4+) is removed
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_cascade_invalidate_silently_skips_missing_dirs`

- **Maps to:** Requirement "CASCADE-INVALIDATION" → Scenario "Target directory does not exist"
- **Type:** unit
- **Given:** `tmp_path` is empty (no phase artifact directories present)
- **When:** `_cascade_invalidate(str(tmp_path), 2)` is called
- **Then:** No exception raised; function completes normally
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_cascade_invalidate_does_not_remove_checkpoint_dir`

- **Maps to:** Requirement "CASCADE-INVALIDATION" → Acceptance criterion "does NOT remove the `.daf-checkpoints/` directory"
- **Type:** unit
- **Given:** `tmp_path` contains `.daf-checkpoints/phase-1-xyz/brand-profile.json`
- **When:** `_cascade_invalidate(str(tmp_path), 0)` is called
- **Then:** `.daf-checkpoints/` and its contents are intact
- **File:** `tests/test_first_publish_agent.py`

---

### RESUME-RESTORE — Restore checkpoint before resuming pipeline

#### Test: `test_cli_resume_calls_restore_before_run_first_publish`

- **Maps to:** Requirement "RESUME-RESTORE" → Scenario "Successful resume from Phase 3 checkpoint"
- **Type:** unit
- **Given:** `tmp_path` is a valid output directory; `CheckpointManager.get_last_valid_checkpoint` returns `{"phase": 3, "path": "...", ...}`; `CheckpointManager.restore` is mocked; `run_first_publish_agent` is mocked
- **When:** `daf init --resume <tmp_path>` is invoked via Typer test client
- **Then:** `mock_cm.restore.assert_called_once_with(output_dir=str(tmp_path), phase=3)` before `mock_run.assert_called_once_with(str(tmp_path), start_phase=4)`; call order: restore before run
- **File:** `tests/test_cli_init.py`

#### Test: `test_cli_resume_exits_with_error_on_corrupt_checkpoint`

- **Maps to:** Requirement "RESUME-RESTORE" → Scenario "Resume with corrupt checkpoint"
- **Type:** unit
- **Given:** `CheckpointManager.get_last_valid_checkpoint` returns an entry; `CheckpointManager.restore` raises `CheckpointCorruptError`
- **When:** `daf init --resume <path>` is invoked
- **Then:** CLI exits with a non-zero code; output contains an error message about the corrupt checkpoint / restart from Phase 1
- **File:** `tests/test_cli_init.py`

#### Test: `test_cli_resume_no_restore_when_no_checkpoints`

- **Maps to:** Requirement "RESUME-RESTORE" → Scenario "Resume with no checkpoints"
- **Type:** unit
- **Given:** `CheckpointManager.get_last_valid_checkpoint` returns `None`
- **When:** `daf init --resume <path>` is invoked
- **Then:** `mock_cm.restore` is NOT called; output contains "No valid checkpoints found" (existing behaviour unchanged)
- **File:** `tests/test_cli_init.py`

---

## Edge Case Tests

#### Test: `test_run_simple_crew_checkpoint_phase_uses_crew_phase_map`

- **Maps to:** Requirement "PRE-CREW-CHECKPOINT" — phase number correctness
- **Type:** unit
- **Given:** `_CREW_PHASE_MAP` defines `"design_to_code": 2` and `"component_factory": 2`
- **When:** `_run_simple_crew("component_factory", ...)` is called
- **Then:** `mock_cm.create` is called with `phase=_CREW_PHASE_MAP["component_factory"]` (not a hardcoded integer); verifies the map drives the phase number, not an inline literal
- **File:** `tests/test_first_publish_agent.py`

#### Test: `test_cascade_invalidate_is_idempotent`

- **Maps to:** Requirement "CASCADE-INVALIDATION" — idempotency / robustness
- **Type:** unit
- **Given:** `tmp_path` contains Phase 4+ artifact dirs
- **When:** `_cascade_invalidate(str(tmp_path), 3)` is called twice
- **Then:** No exception on second call; affected directories remain absent
- **File:** `tests/test_first_publish_agent.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage on `first_publish.py` | ≥ 80% | PRD quality gate requirement |
| Line coverage on `cli.py` (resume path) | ≥ 80% | PRD quality gate requirement |
| Branch coverage on `_run_with_retry` | ≥ 85% | Covers all retry/no-retry / success/fail branches |
| Branch coverage on `_cascade_invalidate` | ≥ 90% | Covers missing-dir and checkpoint-dir skip cases |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_first_publish_agent.py` | modified | Add 11 new test functions for PRE-CREW-CHECKPOINT, PRE-RETRY-RESTORE, CASCADE-INVALIDATION requirements |
| `tests/test_cli_init.py` | modified | Add 3 new test functions for RESUME-RESTORE requirement |
