# Design: p01-project-foundation

## Technical Approach

P01 establishes the Python package that every subsequent proposal extends. The approach is minimal: use modern Python packaging (`pyproject.toml`, `src/` layout), pick Typer as the CLI framework, and stub the `daf init` command with its three invocation patterns — but defer all real logic to later proposals.

The package installs via `pip install -e .`, which registers the `daf` console script. At this stage, running `daf init` acknowledges the invocation and exits. Flags `--profile` and `--resume` are accepted by the CLI parser but print a "not yet implemented" notice.

The directory structure is intentionally shallow:

```
src/daf/
├── __init__.py       # version = "0.1.0"
├── cli.py            # Typer app + init command
├── crews/            # empty — DS Bootstrap et al. added in P03–P09
├── agents/           # empty — agent classes added per proposal
└── tools/            # empty — tool classes added per proposal
```

## Agent vs. Deterministic Decisions

This proposal contains no agent logic. Everything is deterministic scaffolding.

| Capability | Mode | Rationale |
|------------|------|-----------|
| CLI argument parsing | Deterministic (Typer) | Pure data routing — no intelligence needed |
| Flag validation (`--profile` path exists) | Deterministic | File existence check is structural, not semantic |
| `--resume` path validation | Deterministic | Path existence check, deferred to P02 for real use |
| Project skeleton generation | Deterministic | Static file structure — no decision-making involved |

## Model Tier Assignment

No agents are introduced in this proposal.

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| — | — | — | No agents. This is pre-pipeline scaffolding. |

## Architecture Decisions

### Decision: Typer over Click

**Context:** Both Click and Typer are common CLI frameworks for Python. CrewAI packages may introduce transitive Click dependencies.

**Decision:** Use Typer as the primary CLI framework. Typer wraps Click and adds type-annotation-driven argument parsing, which reduces boilerplate and is consistent with the Python typing discipline used throughout the codebase.

**Consequences:** If CrewAI or another dependency pins an incompatible version of Click (Typer's underlying library), we may need to pin `typer[all]` explicitly. This is a manageable risk — Typer's Click compatibility is well-tested.

### Decision: `src/` layout over flat layout

**Context:** Python projects can use a flat layout (package at root) or a `src/` layout (`src/daf/`). Flat layouts are simpler; `src/` layouts prevent accidental imports of the un-installed package during development.

**Decision:** Use `src/daf/` layout throughout.

**Consequences:** All imports are `from daf.xxx import ...`. The package must be installed (`pip install -e .`) before running. This is standard for production Python packages and avoids a class of import bugs.

### Decision: `pyproject.toml` only (no `setup.py`)

**Context:** Legacy Python projects use `setup.py`. Modern packaging uses `pyproject.toml` with a PEP 517/518 build backend.

**Decision:** Use `pyproject.toml` with `[build-system]` pointing to `hatchling` or `setuptools`. No `setup.py`.

**Consequences:** Requires `pip >= 21.3` for editable installs with `pyproject.toml`. This is available in any Python 3.11+ environment per the tech stack requirement (§9).

## Data Flow

This change introduces the CLI entry point. No crew-to-crew file handoffs exist yet.

```
User terminal
  └──► daf init [--profile <path>] [--resume <path>]
         └──► src/daf/cli.py  (stub — exits with "not yet implemented")
```

Once P02 (Interview CLI) and P03 (Brand Discovery Agent) are implemented, the data flow becomes:

```
User terminal ──► daf init ──► Interview (P02) ──► brand-profile.json ──► DS Bootstrap Crew (P03+)
```

## Retry & Failure Behavior

No retry logic in this proposal. The CLI is stateless at this stage — if `daf init` fails, the user simply re-runs it. The `--resume` flag stub (§13.1) is the entry point for future checkpoint-based resumption (P02 implements the logic).

## File Changes

- `pyproject.toml` (new) — project metadata, dependencies (crewai, anthropic, typer), console scripts entry point (`daf = "daf.cli:app"`), dev dependencies (ruff, mypy, pytest)
- `src/daf/__init__.py` (new) — package init, `__version__ = "0.1.0"`
- `src/daf/cli.py` (new) — Typer app, `init` command with `--profile` and `--resume` flags (stubs)
- `src/daf/crews/.gitkeep` (new) — placeholder for future crew modules
- `src/daf/agents/.gitkeep` (new) — placeholder for future agent modules
- `src/daf/tools/.gitkeep` (new) — placeholder for future tool modules
- `README.md` (new) — prerequisites, install steps, first-run instructions, env var configuration
- `.env.example` (new) — `ANTHROPIC_API_KEY=`, `DAF_LOG_LEVEL=INFO`
- `.python-version` (new) — `3.11`
