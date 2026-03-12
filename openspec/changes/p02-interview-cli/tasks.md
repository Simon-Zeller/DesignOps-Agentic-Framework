# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p02-interview-cli`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Ensure dev dependencies are installed: `pip install -e ".[dev]"` — confirm `pytest` and `pytest-cov` are available

## 1. Test Scaffolding (TDD — Red Phase)

> Write all failing tests first. No production code yet.

- [x] 1.1 Create `tests/test_archetypes.py` — archetype defaults completeness test and enterprise-b2b field assertions
- [x] 1.2 Create `tests/test_validator.py` — full §13.3 validation rule set:
  - Required field presence (`name` empty, `name` whitespace-only)
  - Hex color regex: parametrized valid cases (`#1a73e8`, `#fff`, `#ABC`) and invalid cases (`#ZZZZZZ`, `#12345`, `""`)
  - Natural language color description accepted verbatim
  - All `colors.*` sub-fields validated independently (parametrized)
  - `scaleRatio` bounds: `[1.0, 2.0]` valid, outside invalid (parametrized)
  - `baseSize` bounds: `[8, 24]` valid, outside invalid (parametrized)
  - Invalid archetype enum returns error
- [x] 1.3 Create `tests/test_session.py` — `SessionManager` unit tests:
  - Save writes `.daf-session.json` with correct content
  - Load returns saved state
  - Load returns `None` when no file exists
  - Delete removes the file
  - Save is idempotent (same step overwritten)
  - Uses `cwd` by default
- [x] 1.4 Create `tests/test_interview.py` — interview flow and output tests:
  - Full interview via CliRunner produces valid `brand-profile.json` with all required §6 fields
  - Output file is pretty-printed (multi-line)
  - Exit code 0 after success
  - Existing `brand-profile.json` is overwritten
  - `build_profile(state)` omits `componentOverrides` when none provided
  - `collect_overrides()` returns `None` when `$EDITOR` is not set
- [x] 1.5 Update `tests/test_cli_init.py` — extend with `--profile` real behavior tests:
  - Valid profile file exits 0 with confirmation
  - Non-existent file exits 1 with "not found" error
  - Invalid profile (bad archetype) exits 1 with field-level error
  - `--profile` does not create `.daf-session.json`
- [x] 1.6 Verify all new tests **FAIL** (red phase confirmation): `pytest tests/test_archetypes.py tests/test_validator.py tests/test_session.py tests/test_interview.py -v`

## 2. Implementation (TDD — Green Phase)

> Write minimum production code to pass the tests. Follow module split from design.md.

- [x] 2.1 Create `src/daf/archetypes.py` — `ARCHETYPE_DEFAULTS` dict with default values for each of the 5 archetypes, covering all optional §6 fields (colors, typography, spacing, borderRadius, elevation, motion, themes, accessibility, componentScope, breakpoints)
  - Run: `pytest tests/test_archetypes.py` → green
- [x] 2.2 Create `src/daf/validator.py` — `validate_profile(data: dict) -> list[str]` implementing §13.3 rules:
  - Required field check (`name`)
  - Hex color regex for all `colors.*` paths
  - Scale ratio bounds check
  - Base size bounds check
  - Archetype enum membership check
  - Run: `pytest tests/test_validator.py` → green
- [x] 2.3 Create `src/daf/session.py` — `SessionManager(cwd: Path = None)`:
  - `save(step: int, answers: dict) -> None`
  - `load() -> dict | None`
  - `delete() -> None`
  - Session file at `cwd / ".daf-session.json"`
  - Run: `pytest tests/test_session.py` → green
- [x] 2.4 Create `src/daf/interview.py` — `run_interview(cwd: Path = None) -> dict`:
  - `InterviewState` dataclass
  - Steps 1–11 as individual functions, each saving session state on completion
  - On startup: check for existing session and offer resume/restart via Typer prompt
  - Steps 1–2: required fields (name, archetype selection)
  - Steps 3–11: optional with archetype-derived defaults shown via `ARCHETYPE_DEFAULTS`
  - Step 11: `collect_overrides()` — prompt y/N, attempt `$EDITOR`, fall back gracefully
  - `build_profile(state: InterviewState) -> dict` — assembles final §6 dict
  - After step 11: call `validate_profile()`, write `brand-profile.json`, delete session
  - Run: `pytest tests/test_interview.py` → green
- [x] 2.5 Update `src/daf/cli.py` — replace "not yet implemented" stubs:
  - `daf init` (no flags): call `run_interview(cwd=Path.cwd())`
  - `daf init --profile <path>`: load file → `validate_profile()` → print confirmation or errors → exit
  - Run: `pytest tests/test_cli_init.py` → green
- [x] 2.6 Verify full test suite passes: `pytest` → all green

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `validator.py` — consolidate color validation if the hex check appears for multiple fields; extract a `_is_valid_hex(value: str) -> bool` helper
- [x] 3.2 Review `interview.py` — ensure step functions follow a consistent signature: `(state: InterviewState, defaults: dict) -> value`; remove any duplication across steps
- [x] 3.3 Review `session.py` — ensure the session file path is always deterministic and testable; no hard-coded `Path.cwd()` calls outside the constructor
- [x] 3.4 Verify all tests still pass after refactor: `pytest` → all green
- [x] 3.5 Review code against `design.md` decisions — confirm archetype defaults are look-up only, no LLM calls anywhere in the new modules

## 4. Integration & Quality

- [x] 4.1 Run linter: `ruff check src/ tests/` — fix all errors and warnings
- [x] 4.2 Run type checker: `mypy src/daf/` (or `pyright`) — zero type errors
- [x] 4.3 Run full test suite with coverage: `pytest --cov=daf --cov-report=term-missing`
  - Confirm ≥80% line coverage for `archetypes.py`, `validator.py`, `session.py`, `interview.py`, `cli.py`
  - Confirm ≥70% branch coverage
- [x] 4.4 Verify no regressions: existing `tests/test_package.py`, `tests/test_cli_entrypoint.py` still pass
- [x] 4.5 Manual smoke test: `daf init` in a temp directory — step through the interview, accept defaults, confirm `brand-profile.json` is written and is valid JSON

## 5. Git Hygiene

- [x] 5.1 Stage and commit in logical atomic units (conventional commits):
  - `feat: add archetype defaults map (archetypes.py)`
  - `feat: add structural validator for brand profile (validator.py)`
  - `feat: add session persistence manager (session.py)`
  - `feat: implement 11-step brand interview CLI (interview.py)`
  - `feat: wire interview and --profile flag into daf init (cli.py)`
  - `test: add interview CLI test suite (test_archetypes, test_validator, test_session, test_interview)`
  - `test: extend test_cli_init with real --profile validation behavior`
- [x] 5.2 Verify no untracked files remain: `git status` — clean
- [x] 5.3 Rebase on latest main if needed: `git fetch origin && git rebase origin/main`
- [x] 5.4 Push feature branch: `git push origin feat/p02-interview-cli`

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p02-interview-cli`
- [x] 6.3 Push main: `git push origin main`
- [x] 6.4 Delete local feature branch: `git branch -d feat/p02-interview-cli`
- [x] 6.5 Delete remote feature branch: `git push origin --delete feat/p02-interview-cli`
- [x] 6.6 Verify clean state: `git branch -a` — feature branch gone
