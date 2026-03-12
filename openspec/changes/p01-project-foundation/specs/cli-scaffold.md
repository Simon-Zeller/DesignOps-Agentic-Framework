# Specification

## Purpose

This spec defines the behavioral requirements for the DAF Local project foundation — the Python package skeleton, CLI entry point, and developer setup surface. These requirements establish the baseline that all subsequent proposals build upon.

---

## Requirements

### Requirement: Python Package Declaration

The project MUST be declared as an installable Python package via `pyproject.toml` with all runtime dependencies pinned.

#### Acceptance Criteria

- [ ] `pyproject.toml` exists at the project root with valid `[project]` metadata (name, version, requires-python)
- [ ] `crewai`, `anthropic`, and `typer` (or `click`) are listed as runtime dependencies
- [ ] `pip install -e .` succeeds without errors in a clean Python 3.11+ virtual environment
- [ ] `[project.scripts]` registers `daf = "daf.cli:app"` (or equivalent entry point)

#### Scenario: Fresh install

- GIVEN a clean Python 3.11+ virtual environment
- WHEN the developer runs `pip install -e .` from the project root
- THEN all dependencies are resolved and installed without conflicts
- AND the `daf` command becomes available on the PATH

#### Scenario: Missing Python version

- GIVEN a Python version below 3.11
- WHEN the developer attempts `pip install -e .`
- THEN `pip` raises a version incompatibility error before installing anything

---

### Requirement: CLI Entry Point Registration

The `daf` command MUST be registered as a console script and respond to `--help` without errors.

#### Acceptance Criteria

- [ ] `daf --help` exits with code 0 and prints usage information
- [ ] `daf init --help` exits with code 0 and lists `--profile` and `--resume` flags with descriptions
- [ ] `daf` without subcommands prints top-level usage (not an unhandled exception)

#### Scenario: Top-level help

- GIVEN `daf` is installed via `pip install -e .`
- WHEN the user runs `daf --help`
- THEN the terminal prints usage text listing `init` as a subcommand
- AND exits with code 0

#### Scenario: Subcommand help

- GIVEN `daf` is installed
- WHEN the user runs `daf init --help`
- THEN the terminal prints usage text for the `init` subcommand
- AND lists `--profile` and `--resume` as optional flags with descriptions

#### Scenario: No arguments

- GIVEN `daf` is installed
- WHEN the user runs `daf` with no arguments
- THEN the CLI displays the top-level help text (or a helpful prompt)
- AND exits cleanly without a Python traceback

---

### Requirement: `daf init` Stub Invocation

The `daf init` command MUST accept invocation in all three forms defined in §13.1 without crashing.

#### Acceptance Criteria

- [ ] `daf init` (interactive mode) runs without exception and prints a placeholder message indicating the interview is not yet implemented
- [ ] `daf init --profile ./path.json` accepts the flag and acknowledges the path
- [ ] `daf init --resume ./output-dir` accepts the flag and acknowledges the path
- [ ] All three forms exit with code 0

#### Scenario: Interactive mode stub

- GIVEN `daf` is installed
- WHEN the user runs `daf init`
- THEN the CLI prints a message such as "Interview not yet implemented" (or similar placeholder)
- AND exits with code 0

#### Scenario: Non-interactive mode stub (`--profile`)

- GIVEN `daf` is installed
- WHEN the user runs `daf init --profile ./my-profile.json`
- THEN the CLI acknowledges the `--profile` flag (e.g., prints "Profile mode: not yet implemented")
- AND exits with code 0
- AND does NOT require `./my-profile.json` to exist at this stage (path validation is deferred to P02)

#### Scenario: Resume mode stub (`--resume`)

- GIVEN `daf` is installed
- WHEN the user runs `daf init --resume ./output-dir`
- THEN the CLI acknowledges the `--resume` flag (e.g., prints "Resume mode: not yet implemented")
- AND exits with code 0

#### Scenario: Unknown flag

- GIVEN `daf` is installed
- WHEN the user runs `daf init --unknown-flag`
- THEN the CLI prints an error message indicating the unknown option
- AND exits with a non-zero code (Typer/Click default behavior)

---

### Requirement: Project Directory Layout

The `src/daf/` package MUST follow the specified directory structure so subsequent proposals can extend it without restructuring.

#### Acceptance Criteria

- [ ] `src/daf/__init__.py` exists and exports `__version__`
- [ ] `src/daf/cli.py` exists and contains the Typer app and `init` command
- [ ] `src/daf/crews/` directory exists (may contain only a `.gitkeep`)
- [ ] `src/daf/agents/` directory exists (may contain only a `.gitkeep`)
- [ ] `src/daf/tools/` directory exists (may contain only a `.gitkeep`)
- [ ] `from daf.cli import app` succeeds after `pip install -e .`

#### Scenario: Package import

- GIVEN `daf` is installed via `pip install -e .`
- WHEN a Python interpreter runs `import daf`
- THEN the import succeeds without errors
- AND `daf.__version__` returns a valid semver string

#### Scenario: Module isolation

- GIVEN `daf` is installed via `pip install -e .`
- WHEN the developer runs tests from the project root (not from `src/`)
- THEN Python imports `daf` from the installed package (not from the raw `src/daf/` directory)
- AND no `ModuleNotFoundError` occurs due to layout ambiguity

---

### Requirement: Developer Setup Documentation

A `README.md` MUST exist at the project root with complete setup instructions for a new developer.

#### Acceptance Criteria

- [ ] `README.md` lists prerequisites: Python ≥3.11, Node (for downstream tooling), and `ANTHROPIC_API_KEY`
- [ ] `README.md` includes the exact command sequence to set up a dev environment: create venv, `pip install -e .`, configure `.env`
- [ ] `README.md` includes a first-run example: `daf init`
- [ ] `.env.example` exists at the project root with `ANTHROPIC_API_KEY=` and at least one other relevant variable
- [ ] A developer following only the README instructions can reach a working `daf --help` output

#### Scenario: New developer onboarding

- GIVEN a developer has cloned the repo with no prior DAF knowledge
- WHEN they follow the README instructions exactly
- THEN they have a working `daf` command available without seeking additional guidance
- AND they understand what environment variables are required

#### Scenario: Missing API key

- GIVEN a developer has installed `daf` but has not set `ANTHROPIC_API_KEY`
- WHEN they follow the `.env.example` to configure their environment
- THEN they know the correct variable name and format to set
