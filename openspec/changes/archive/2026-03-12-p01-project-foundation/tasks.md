# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p01-project-foundation`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm Python ≥3.11 is active (`python --version`)

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

- [x] 1.1 Create `tests/__init__.py` (empty)
- [x] 1.2 Create `tests/test_package.py` with two tests:
  - `test_import_daf` — asserts `import daf` succeeds and `daf.__version__` matches `\d+\.\d+\.\d+`
  - `test_import_cli_app` — asserts `from daf.cli import app` succeeds and `app` is callable
- [x] 1.3 Create `tests/test_cli_entrypoint.py` with subprocess-level smoke tests:
  - `test_daf_help_exits_zero` — runs `daf --help` via `subprocess.run`, asserts exit code 0 and `init` in stdout
  - `test_daf_init_help_lists_flags` — runs `daf init --help`, asserts exit code 0, `--profile` and `--resume` in stdout
  - `test_daf_no_args_no_traceback` — runs `daf` with no args, asserts no Python traceback in stderr
- [x] 1.4 Create `tests/test_cli_init.py` with unit tests using Typer's `CliRunner`:
  - `test_init_interactive_stub_exits_zero`
  - `test_init_profile_flag_exits_zero`
  - `test_init_resume_flag_exits_zero`
  - `test_init_profile_does_not_require_file_to_exist`
  - `test_init_unknown_flag_nonzero_exit`
  - `test_init_combined_flags_documents_behavior` (regression anchor)
- [x] 1.5 Run `pytest` — verify **all new tests FAIL** (red phase confirmation — `ModuleNotFoundError` or `FileNotFoundError` is expected)

## 2. Implementation (TDD — Green Phase)

- [x] 2.1 Create `pyproject.toml` at project root:
  - `[project]`: name=`daf`, version=`0.1.0`, requires-python=`>=3.11`
  - `[project.dependencies]`: `crewai`, `anthropic`, `typer[all]`
  - `[project.optional-dependencies]` dev group: `pytest`, `pytest-cov`, `ruff`, `mypy`
  - `[project.scripts]`: `daf = "daf.cli:app"`
  - `[build-system]`: hatchling or setuptools
- [x] 2.2 Create `src/daf/__init__.py`:
  - Set `__version__ = "0.1.0"`
- [x] 2.3 Create `src/daf/cli.py`:
  - Initialize Typer app: `app = typer.Typer(name="daf", help="DesignOps Agentic Framework CLI")`
  - Define `init` command with `--profile: Optional[str] = None` and `--resume: Optional[str] = None`
  - Stub body: print appropriate placeholder messages for each flag combination; exit cleanly
- [x] 2.4 Create placeholder directories with `.gitkeep`:
  - `src/daf/crews/.gitkeep`
  - `src/daf/agents/.gitkeep`
  - `src/daf/tools/.gitkeep`
- [x] 2.5 Install the package: `pip install -e ".[dev]"`
- [x] 2.6 Run `pytest` — verify **all tests PASS** (green phase confirmation)

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `cli.py` against design.md — ensure flag descriptions in `typer.Option(...)` match §13.1 invocation semantics
- [x] 3.2 Ensure placeholder messages are user-friendly (not bare `pass` or `print("")`)
- [x] 3.3 Run `pytest` again — confirm all tests still pass

## 4. Developer Setup Files

- [x] 4.1 Create `README.md`:
  - Prerequisites section: Python ≥3.11, Node (for downstream output), `ANTHROPIC_API_KEY`
  - Setup steps: `python -m venv .venv`, `source .venv/bin/activate`, `pip install -e ".[dev]"`, `cp .env.example .env`
  - First run: `daf init`
  - Pointer to `.env.example` for API key configuration
- [x] 4.2 Create `.env.example`:
  - `ANTHROPIC_API_KEY=`
  - `DAF_LOG_LEVEL=INFO`
- [x] 4.3 Create `.python-version` containing `3.11`

## 5. Integration & Quality

- [x] 5.1 Run `ruff check src/ tests/` — fix all lint errors (zero warnings)
- [x] 5.2 Run `mypy src/daf/` — fix all type errors
- [x] 5.3 Run full test suite with coverage: `pytest --cov=daf --cov-report=term-missing`
- [x] 5.4 Verify line coverage ≥80% for `src/daf/cli.py` and `src/daf/__init__.py`
- [x] 5.5 Confirm `daf --help` and `daf init --help` work correctly in the terminal (not via CliRunner)

## 6. Git Hygiene

- [x] 6.1 Stage all new files with atomic commits using conventional commit format:
  - `chore: scaffold python project with pyproject.toml`
  - `feat: add daf cli entry point with init command stub`
  - `docs: add README and .env.example`
  - `test: add test suite for cli scaffold`
- [x] 6.2 Confirm no untracked files remain (`git status`)
- [x] 6.3 Push feature branch: `git push origin feat/p01-project-foundation`

## 7. Ready for Verification

- [x] 7.1 All tasks above are checked
- [x] 7.2 Proceed to verification checklist (`verification.md`)
