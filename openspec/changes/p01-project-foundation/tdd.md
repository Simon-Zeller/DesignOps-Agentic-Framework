# TDD Plan: p01-project-foundation

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This proposal is pure Python project scaffolding and CLI skeleton — no agent logic, no LLM calls, no file I/O beyond stubs. The test suite uses **pytest** (not Vitest, which is for the generated React output). Tests run against the installed `daf` package.

Two complementary test types are used:

1. **Unit tests** — test the CLI command routing directly by invoking Typer's `CliRunner` (or Click's `CliRunner`) without subprocess overhead
2. **Integration smoke tests** — invoke `daf` as a subprocess to verify the console script entry point is correctly registered and exits cleanly

Coverage target: ≥80% line coverage per PRD quality gate (§3.8 `qualityGates.minTestCoverage`).

---

## Test Cases

### CLI Entry Point

#### Test: `daf --help` exits 0

- **Maps to:** Requirement "CLI Entry Point Registration" → Scenario "Top-level help"
- **Type:** integration
- **Given:** `daf` is installed via `pip install -e .`
- **When:** the process runs `daf --help`
- **Then:** exit code is `0` and stdout contains the word `init`
- **File:** `tests/test_cli_entrypoint.py`

#### Test: `daf init --help` exits 0 and lists flags

- **Maps to:** Requirement "CLI Entry Point Registration" → Scenario "Subcommand help"
- **Type:** integration
- **Given:** `daf` is installed
- **When:** the process runs `daf init --help`
- **Then:** exit code is `0`, stdout contains `--profile`, stdout contains `--resume`
- **File:** `tests/test_cli_entrypoint.py`

#### Test: `daf` with no arguments does not crash

- **Maps to:** Requirement "CLI Entry Point Registration" → Scenario "No arguments"
- **Type:** integration
- **Given:** `daf` is installed
- **When:** the process runs `daf` with no arguments
- **Then:** exit code is `0` (help text shown) or a consistent non-zero without a Python traceback
- **File:** `tests/test_cli_entrypoint.py`

---

### `daf init` Stub

#### Test: `daf init` (interactive mode) exits 0

- **Maps to:** Requirement "`daf init` Stub Invocation" → Scenario "Interactive mode stub"
- **Type:** unit
- **Given:** Typer CliRunner with no arguments
- **When:** the runner invokes `app(["init"])` 
- **Then:** result exit code is `0` and output contains a non-empty placeholder string
- **File:** `tests/test_cli_init.py`

#### Test: `daf init --profile ./some/path.json` exits 0

- **Maps to:** Requirement "`daf init` Stub Invocation" → Scenario "Non-interactive mode stub (`--profile`)"
- **Type:** unit
- **Given:** Typer CliRunner
- **When:** the runner invokes `app(["init", "--profile", "./some/path.json"])`
- **Then:** result exit code is `0`
- AND output acknowledges the `--profile` flag (contains path or flag name)
- **File:** `tests/test_cli_init.py`

#### Test: `daf init --resume ./output-dir` exits 0

- **Maps to:** Requirement "`daf init` Stub Invocation" → Scenario "Resume mode stub (`--resume`)"
- **Type:** unit
- **Given:** Typer CliRunner
- **When:** the runner invokes `app(["init", "--resume", "./output-dir"])`
- **Then:** result exit code is `0`
- AND output acknowledges the `--resume` flag
- **File:** `tests/test_cli_init.py`

#### Test: `--profile` does not require the file to exist

- **Maps to:** Requirement "`daf init` Stub Invocation" → Scenario "Non-interactive mode stub (`--profile`)"
- **Type:** unit
- **Given:** Typer CliRunner and the path `./nonexistent-profile.json` does not exist on disk
- **When:** the runner invokes `app(["init", "--profile", "./nonexistent-profile.json"])`
- **Then:** result exit code is `0` (path validation is deferred to P02)
- AND no `FileNotFoundError` is raised
- **File:** `tests/test_cli_init.py`

---

### Package Layout & Import

#### Test: `import daf` succeeds

- **Maps to:** Requirement "Project Directory Layout" → Scenario "Package import"
- **Type:** unit
- **Given:** `daf` is installed via `pip install -e .`
- **When:** Python executes `import daf`
- **Then:** no `ImportError` is raised
- AND `daf.__version__` is a non-empty string matching semver pattern (`\d+\.\d+\.\d+`)
- **File:** `tests/test_package.py`

#### Test: `from daf.cli import app` succeeds

- **Maps to:** Requirement "Project Directory Layout" → Scenario "Package import"
- **Type:** unit
- **Given:** `daf` is installed
- **When:** Python executes `from daf.cli import app`
- **Then:** no `ImportError` is raised
- AND `app` is a Typer application instance (has `command` attribute or is callable)
- **File:** `tests/test_package.py`

---

## Edge Case Tests

#### Test: Unknown flag produces non-zero exit

- **Maps to:** Requirement "`daf init` Stub Invocation" → Scenario "Unknown flag"
- **Type:** unit
- **Given:** Typer CliRunner
- **When:** the runner invokes `app(["init", "--unknown-flag"])`
- **Then:** result exit code is non-zero
- AND output contains an error message mentioning the unrecognized option
- **File:** `tests/test_cli_init.py`

#### Test: `--profile` and `--resume` cannot be combined (if mutually exclusive)

- **Maps to:** Requirement "`daf init` Stub Invocation" → flag conflict edge case
- **Type:** unit
- **Given:** Typer CliRunner
- **When:** the runner invokes `app(["init", "--profile", "./p.json", "--resume", "./dir"])`
- **Then:** either exits 0 (flags coexist for now, conflict enforced in P02) or exits non-zero with a clear error — either behavior is acceptable; this test documents current behavior as a regression anchor
- **File:** `tests/test_cli_init.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement (§3.8 `qualityGates.minTestCoverage`) |
| Branch coverage | ≥70% | Covers all flag-routing conditional paths |
| A11y rules passing | N/A | CLI-only — no UI components in this proposal |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/__init__.py` | new | Empty init to make `tests/` a package |
| `tests/test_package.py` | new | Import correctness and `__version__` shape |
| `tests/test_cli_entrypoint.py` | new | Subprocess-level smoke tests for `daf --help` and `daf init --help` |
| `tests/test_cli_init.py` | new | Unit tests for `init` command: all three invocation modes, unknown flags, flag conflict edge case |
