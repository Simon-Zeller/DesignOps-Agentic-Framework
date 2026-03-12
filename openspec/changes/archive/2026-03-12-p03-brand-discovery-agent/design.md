# Design: p03-brand-discovery-agent

## Technical Approach

P03 implements Agent 1 (Brand Discovery Agent) as a CrewAI `Agent` with four deterministic tools, wired into a Task that transforms a raw `brand-profile.json` into a validated, enriched, fully-specified `brand-profile.json`. After the task completes, a Human Gate prompt asks the user to approve the result before the pipeline can advance.

The implementation adds one new module for the agent (`src/daf/agents/brand_discovery.py`) and four tool modules under `src/daf/tools/`. It extends `cli.py` with a `daf generate` command that loads the raw profile, invokes the agent task, and runs the gate prompt.

**Execution flow:**

```
daf generate [--profile <path>] [--yes]
  1. Load brand-profile.json (from cwd or --profile flag)
  2. Instantiate BrandDiscoveryAgent with tools
  3. Create Task T1 (validate → resolve → check → fill → return enriched profile)
  4. Run CrewAI Crew([BrandDiscoveryAgent]) with task T1
  5. Parse Pydantic output → enriched BrandProfile model
  6. Show Human Gate summary prompt (skip if --yes)
  7. Write final brand-profile.json; exit 0 (approved) or 1 (rejected)
```

Each tool is a deterministic Python class registered with CrewAI. The agent uses Claude Sonnet (Tier 2) to handle reasoning tasks: interpreting natural language color descriptions into hex intent notes, resolving archetype edge cases, and narrating why changes were made.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| JSON Schema validation of raw profile | Deterministic (`jsonschema`) | Pure structural check against §6 schema — no inference needed |
| Archetype default resolution | Deterministic (look-up table) | Enum-keyed dict of defaults; no ambiguity |
| Consistency rule enforcement | Deterministic (predicate list) | Rules are explicit and finite; no reasoning required |
| Default field filling | Deterministic (dict merge) | Merge operation; archetype defaults provide the values |
| Natural language color interpretation | Agent (LLM) | Translating "a warm corporate red" into a hex intent annotation requires semantic reasoning |
| Contradiction explanation | Agent (LLM) | Generating human-readable explanations for detected contradictions requires prose reasoning |
| Enrichment narrative | Agent (LLM) | Describing *why* each archetype default was applied, for display at the Human Gate |
| Human Gate summary rendering | Deterministic | Formatting the enriched profile as a readable diff/summary |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Brand Discovery Agent (1) | Tier 2 — Analytical | Claude Sonnet | Analytical work: interprets structured input, reasons about consistency, produces structured output. Not generative (no large code/prose artifacts). Matches §3.7 Tier 2 assignment. |

## Architecture Decisions

### Decision: Tools are deterministic; agent wraps for reasoning-enriched output

**Context:** The four core operations (schema validation, archetype resolution, consistency checking, default filling) are deterministic. Agent 1 is classified as Tier 2 (Analytical), meaning it reasons over structured inputs — not generative.

**Decision:** Each operation is a separate CrewAI `BaseTool` with typed input/output. The agent's reasoning layer adds: natural language color resolution notes, contradiction explanations in plain English, and an enrichment narrative. The final output merges the deterministic operation results with the agent's prose annotations.

**Consequences:** Tools are independently testable without a live LLM. Agent tests mock the LLM and verify tool orchestration. Integration tests exercise the full agent with a real Claude call (gated behind `@pytest.mark.integration`).

### Decision: Pydantic output model (`BrandProfile`) enforces §6 schema over LLM output

**Context:** CrewAI tasks with `output_json` or `output_pydantic` enforce structured output. Without this, the LLM could hallucinate extra fields or omit required ones.

**Decision:** Define a Pydantic `BrandProfile` model that mirrors the §6 schema exactly. Assign it as `output_pydantic=BrandProfile` on the CrewAI Task. Extra fields are stripped; missing fields raise ValidationError caught by the task runner.

**Consequences:** The enriched profile written to disk is always §6-conformant. LLM output format errors become recoverable task errors, not silent corruption.

### Decision: Human Gate prompt is CLI-level, not inside the CrewAI task

**Context:** The Human Gate (§5) requires pausing execution for a human to review the full profile before generation begins. CrewAI tasks are designed to run to completion; interrupting them mid-execution for user approval is anti-pattern.

**Decision:** The CrewAI task runs to completion and returns the enriched `BrandProfile`. The gate prompt runs as CLI code *after* the task completes, before writing the final file and triggering the pipeline. This keeps CrewAI fully autonomous and the human interaction at the CLI boundary.

**Consequences:** The `--yes` flag can skip the gate without touching task logic. The gate can be unit-tested without CrewAI. The separation matches the architectural intent in §4.1 ("all intelligence in the agent, gate at the CLI boundary").

### Decision: Separate `src/daf/agents/` and `src/daf/tools/` package structure

**Context:** P01 established `src/daf/`. P02 added `interview.py`, `session.py`, `validator.py`, `archetypes.py`. Agent and tool modules are a different concern.

**Decision:** Introduce `src/daf/agents/` for CrewAI Agent definitions and `src/daf/tools/` for tool implementations. Each agent and tool gets its own module file.

**Consequences:** Clear separation between orchestration code (agents) and execution code (tools). Follows CrewAI convention. Future agents (P04+) add modules under `agents/` without touching existing files.

### Decision: `--yes` flag auto-approves for CI/CD usage

**Context:** §13.5 specifies that `daf init --profile` enables non-interactive / CI/CD usage. Agent 1's Human Gate would block CI pipelines that pass a validated profile.

**Decision:** `daf generate --yes` skips the approval prompt and unconditionally writes the enriched profile. Documented in CLI help text and README.

**Consequences:** CI/CD can use `daf generate --profile ./profile.json --yes` for fully non-interactive runs. The gate is not bypassed in the security sense — Agent 1 still validates and enriches the profile; only the interactive confirmation is skipped.

## Data Flow

```
[P02 Interview CLI]
  └──writes──► brand-profile.json (raw, pre-validation)
                    │
                    ▼
[daf generate]
  └── loads brand-profile.json
        │
        ▼
[BrandDiscoveryAgent — Task T1]
  ├── BrandProfileSchemaValidator ──► validation result (errors | ok)
  ├── ArchetypeResolver           ──► archetype defaults dict
  ├── ConsistencyChecker          ──► contradiction list (errors + warnings)
  └── DefaultFiller               ──► fully-specified profile dict
        │
        ▼ (LLM reasoning: translate color descriptions, explain contradictions, narrate enrichment)
        │
        ▼ Pydantic BrandProfile output
  │
  ▼
[Human Gate prompt] ──► y → write final brand-profile.json ──► exit 0
                     └──► N → print instruction to re-run daf init ──► exit 1
                    │
                    ▼ (on approval)
[Awaits P06: First Publish Agent]
  └──reads──► brand-profile.json (validated, enriched)
              → triggers full generation pipeline
```

```
DS Bootstrap Crew ──writes──► brand-profile.json (validated) ──reads──► Token Engine Crew
                                                               ──reads──► Design-to-Code Crew
                                                               ──reads──► Component Factory Crew
                                                               ──reads──► Documentation Crew
                                                               ──reads──► Governance Crew
                                                               ──reads──► Analytics Crew
                                                               ──reads──► AI Semantic Layer Crew
                                                               ──reads──► Release Crew
```

## Retry & Failure Behavior

Agent 1 is the first agent in Phase 1. The retry protocol (§3.4) defines how Phase 1 agent failures are handled via the First Publish Agent (6). However, P03's scope ends before the pipeline starts — there is no downstream validator to reject Agent 1's output and trigger a retry in the §3.4 sense.

**Within-task failure modes and handling:**

| Failure | Behavior |
|---------|----------|
| `BrandProfileSchemaValidator` finds missing required fields | Task raises `ValidationError`; CLI prints field-level errors and exits with message "Run `daf init` to fix the profile." |
| `ConsistencyChecker` finds `error`-severity contradictions | Agent LLM generates an explanation; task returns a failed result with structured contradiction details; CLI prints contradictions and exits with code 1 |
| `ConsistencyChecker` finds `warning`-severity contradictions | Agent continues; contradictions are included in the enriched profile's `_warnings` annotation field and shown at the Human Gate |
| LLM call fails (API error, timeout) | CrewAI retries with backoff up to 3 times (CrewAI default); if all fail, CLI prints "LLM unavailable" and exits with code 1 |
| Pydantic validation fails on LLM output | Task re-runs with a correction prompt appended (CrewAI structured output retry); max 2 attempts |
| Human Gate: user rejects profile | CLI exits code 1 with message "Profile rejected. Edit your answers and re-run `daf init`." |

The First Publish Agent (6) and its cross-phase retry routing apply only once generation is running — they are not invoked by this change.

## File Changes

- `src/daf/agents/__init__.py` (new) — package marker
- `src/daf/agents/brand_discovery.py` (new) — `BrandDiscoveryAgent` CrewAI Agent definition, Task T1, Crew wrapper
- `src/daf/tools/__init__.py` (new) — package marker
- `src/daf/tools/brand_profile_validator.py` (new) — `BrandProfileSchemaValidator` tool; JSON Schema validation against §6 schema
- `src/daf/tools/archetype_resolver.py` (new) — `ArchetypeResolver` tool; returns complete defaults dict per archetype
- `src/daf/tools/consistency_checker.py` (new) — `ConsistencyChecker` tool; evaluates predicate rules, returns structured contradiction list
- `src/daf/tools/default_filler.py` (new) — `DefaultFiller` tool; merges archetype defaults into profile dict
- `src/daf/models.py` (new) — `BrandProfile` Pydantic model mirroring §6 schema; used as CrewAI task `output_pydantic`
- `src/daf/cli.py` (modified) — add `daf generate` command; load profile, invoke agent, run Human Gate prompt
- `tests/test_brand_discovery_agent.py` (new) — unit + integration tests for Agent 1 and all four tools
