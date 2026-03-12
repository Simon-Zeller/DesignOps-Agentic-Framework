# Design: p02-interview-cli

## Technical Approach

P02 implements the 11-step brand interview described in §13. The CLI is a pure Python module (`src/daf/interview.py`) — no CrewAI agents are invoked here. It interacts directly with the terminal, collects answers, persists session state, validates structural constraints, and writes `brand-profile.json`.

The existing `daf init` command in `cli.py` is the entry point. P02 replaces the current "not yet implemented" stubs with real logic:

1. **Archetype defaults map** (`src/daf/archetypes.py`) — a Python dict keyed by archetype name, providing default values for every optional §6 field. Used at each step to show "press Enter to accept default" hints.
2. **Interview runner** (`src/daf/interview.py`) — orchestrates the 11-step flow. Each step is a function. Steps 1–2 are required; steps 3–11 are optional with archetype-derived defaults. Typer's `typer.prompt()` is used for single-value inputs; a custom `select()` helper wraps Typer for single-choice selection (archetype, density, radius, etc.).
3. **Session persistence** (`src/daf/session.py`) — a thin wrapper that serializes the current interview state to `.daf-session.json` after each step completes. On `daf init` startup, the session module checks for an existing file and offers resume/restart.
4. **Structural validator** (`src/daf/validator.py`) — applies the §13.3 rules: required field presence, hex color syntax, scale ratio bounds, base size bounds, archetype enum membership. Returns a list of validation errors; the interview re-prompts failing fields.
5. **Profile writer** — once all steps pass validation, `interview.py` serializes the complete profile to `brand-profile.json` in the current working directory (§13.4) and deletes `.daf-session.json`.

The `--profile` flag path in `cli.py` is updated to load the file, run it through the structural validator, print a confirmation, and exit (full semantic validation deferred to Agent 1, P03).

**No LLM is called in this change.** Natural language color descriptions (e.g., `"a professional blue"`) are stored verbatim as strings — resolution to hex is the Brand Discovery Agent's responsibility (P03).

## Agent vs. Deterministic Decisions

This proposal contains no agent logic. Everything is deterministic.

| Capability | Mode | Rationale |
|------------|------|-----------|
| Collecting user input (steps 1–11) | Deterministic (Typer prompts) | Pure Q&A flow — no reasoning required |
| Archetype default resolution for prompts | Deterministic (look-up table) | Enum-keyed dict; no ambiguity |
| Session persistence (`.daf-session.json`) | Deterministic (JSON serialization) | Structural data, no inference needed |
| Structural validation (hex, bounds, required) | Deterministic | Rule-based checks per §13.3 |
| Natural language color inputs | Stored verbatim | Resolution deliberately deferred to Agent 1 (Brand Discovery Agent) via archetype resolver |
| `--profile` file load + minimal validation | Deterministic | File read + JSON parse + structural check |
| `brand-profile.json` write | Deterministic (json.dumps) | Serialization of collected data |

## Model Tier Assignment

No agents are introduced in this proposal.

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| — | — | — | No agents. The interview CLI is pre-pipeline, outside CrewAI. |

## Architecture Decisions

### Decision: Split interview logic into `interview.py`, not inline in `cli.py`

**Context:** `cli.py` is the Typer entry point. Embedding 11 steps of interview logic into the command function would make it hard to test and hard for P03 to wire up.

**Decision:** Extract all interview logic into `src/daf/interview.py`. `cli.py` calls `run_interview()` from there. `session.py` and `validator.py` are further separated for testability.

**Consequences:** Interview can be unit-tested without invoking the CLI parser. Session and validation logic can be swapped independently.

### Decision: Session file lives in the current working directory, not `~/.daf/`

**Context:** `daf init` is intended to be run from the intended project output directory. The session file should be co-located with where `brand-profile.json` will be written.

**Decision:** `.daf-session.json` is written to `Path.cwd() / ".daf-session.json"`.

**Consequences:** Two concurrent `daf init` runs in the same directory would overwrite each other's session. This is an acceptable constraint for a local dev tool — document it in the README.

### Decision: Step 11 (component overrides) uses `$EDITOR` fallback, not inline prompting

**Context:** Component overrides are a nested JSON structure (§6) — impractical to collect field-by-field in the terminal. The PRD describes them as "advanced, optional."

**Decision:** Step 11 asks "Add component overrides? (y/N)". If yes, attempt to open `$EDITOR` with a pre-populated JSON template. If `$EDITOR` is unset or unavailable, skip with a note to add overrides manually before running Agent 1. If the editor is closed with a valid JSON object, parse and attach it to the profile.

**Consequences:** Most users skip step 11 (correct behavior). Power users with `$EDITOR` set get a real editing experience. No dependency on `questionary` or a TUI library.

### Decision: Structural validation in `validator.py` — no duplication of agent intelligence

**Context:** §13.3 explicitly scopes CLI validation to structural rules only. Semantic validation (contradictions, default enrichment) belongs to Agent 1.

**Decision:** `validator.py` enforces exactly the §13.3 rule set — nothing more. It does not attempt to detect contradiction between, e.g., `density: compact` and archetype defaults.

**Consequences:** The CLI will accept technically valid but semantically inconsistent profiles. Agent 1 catches these at the next stage. This is the intended design (§4.1).

## Data Flow

```
User terminal
  └──► daf init
         ├── (session exists?) ──► offer resume from step N or restart
         └── run_interview()  [src/daf/interview.py]
               ├── step 1..11  ──► session.save()  ──► .daf-session.json (per step)
               └── validator.validate()
                     └── (pass) ──► write brand-profile.json
                                    delete .daf-session.json
                                    exit 0
```

```
User terminal
  └──► daf init --profile ./my-profile.json
         └── load file ──► validator.validate() ──► confirm + exit 0
                                                     (Agent 1 does semantic validation, P03)
```

Post-P02 handoff (P03 wires this up):

```
brand-profile.json  ──reads──►  DS Bootstrap Crew / Agent 1 (Brand Discovery Agent)
```

## Retry & Failure Behavior

The interview CLI has no retry protocol (§3.4 applies to CrewAI agents, not the pre-pipeline CLI).

- **Structural validation failure:** Re-prompt the failing field inline. The user cannot proceed until required fields are non-empty and validated fields pass their rules.
- **Session interruption (Ctrl+C, terminal close):** `.daf-session.json` preserves the last completed step. Re-running `daf init` in the same directory detects the file and offers resume.
- **`--profile` file not found:** Exit with a clear error message and code 1. No partial state written.
- **`--profile` file fails validation:** Print field-level errors and exit with code 1. The file is not written or mutated.
- **Step 11 editor failure:** Silently skip component overrides, log a warning, and continue. The profile is written without `componentOverrides`.

## File Changes

- `src/daf/archetypes.py` (new) — archetype defaults map; keys are archetype enum values, values are dicts of §6 field defaults
- `src/daf/interview.py` (new) — `run_interview()` function orchestrating 11 steps; `InterviewState` dataclass
- `src/daf/session.py` (new) — `SessionManager`: save, load, delete `.daf-session.json`; detect existing session on startup
- `src/daf/validator.py` (new) — `validate_profile(data: dict) -> list[str]`; applies §13.3 structural rules
- `src/daf/cli.py` (modified) — replace "not yet implemented" stubs with calls to `run_interview()` and `--profile` load+validate
- `tests/test_interview.py` (new) — unit tests for each interview step, archetype defaults, session persistence, validation rules
- `tests/test_validator.py` (new) — parametrized tests for each §13.3 validation rule
- `tests/test_cli_init.py` (modified) — extend existing tests to cover real interview invocation paths
