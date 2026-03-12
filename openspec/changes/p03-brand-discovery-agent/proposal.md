# Proposal: p03-brand-discovery-agent

## Intent

P02 implemented the interview CLI that collects raw brand input and writes `brand-profile.json`. That file is intentionally dumb — the CLI performs only structural validation (required fields, hex validity, numeric bounds). All intelligence is deliberately deferred to Agent 1: Brand Discovery Agent.

Without Agent 1, the raw profile is never validated for semantic consistency, contradictions are never caught, archetype-derived defaults are never filled in for omitted fields, and the pipeline has no validated input to run from. The Human Gate (Brand Profile approval) also lives in this change — without it, the user would have no opportunity to review and approve the enriched profile before generation commits.

P03 implements Agent 1 (Brand Discovery Agent) of the DS Bootstrap Crew. This is the first CrewAI agent in the DAF system and the semantic entry point to the entire generation pipeline.

## Scope

### In scope

- **Agent 1: Brand Discovery Agent** — CrewAI agent with role, goal, backstory, and tool assignments (§4.1)
- **Brand Profile Schema Validator tool** — JSON Schema validation of the raw `brand-profile.json` against the §6 schema; structural errors become structured rejections
- **Archetype Resolver tool** — maps each archetype (`enterprise-b2b`, `consumer-b2c`, `mobile-first`, `multi-brand`, `custom`) to a complete defaults object for all optional §6 fields; fills in omitted fields with archetype-correct values
- **Consistency Checker tool** — semantic rule engine that detects contradictions in the validated profile (e.g., `density: compact` + `spacing.density: spacious`, `accessibility: AAA` + unsupported color contrast pair, `archetype: mobile-first` + `componentScope: comprehensive`, `motion: expressive` + `motion: none` equivalent conflicts)
- **Default Filler tool** — applies archetype defaults to any field the user left unspecified during the interview; produces a complete, fully-specified `brand-profile.json`
- **Human Gate 1: Brand Profile Approval** — CLI prompt shown after Agent 1 outputs the enriched profile; user reviews the final `brand-profile.json` and either approves (triggers pipeline) or rejects (re-enters interview); this is the first and most important human gate (§5)
- **`daf generate` command stub** — CLI entry point that invokes Agent 1 with the raw `brand-profile.json` and handles the approval gate; generation pipeline invocation deferred to P06 (First Publish Agent)
- **Unit tests** for all four tools and the gate prompt logic

### Out of scope

- DS Bootstrap Crew task wiring (tasks T2–T6 for Agents 2–6) — subsequent changes
- Triggering the generation pipeline after approval — P06 (First Publish Agent)
- Natural language color resolution to hex — Agent 1 stores the string as-is; the Token Foundation Agent (2) resolves it
- Multi-brand `brands[]` validation beyond basic non-empty array check — P10
- Resume-from-checkpoint (`--resume` flag) — P08
- `daf init --profile` passthrough for CI/CD — already wired in P02; P03 adds the downstream invocation

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap (Crew 1) | Agent 1: Brand Discovery Agent | **Implemented here.** Role, goal, backstory, tools, and task T1 are all new. |
| DS Bootstrap (Crew 1) | Agent 6: First Publish Agent | Downstream receiver of the validated profile — not changed here, but the I/O contract is established. |
| All downstream crews | All agents that read `brand-profile.json` | The enriched `brand-profile.json` produced here is the single source of truth for all 8 downstream crews (§3.6). This change defines that contract in code for the first time. |

## PRD References

- **§4.1 DS Bootstrap Crew — Agent 1** — Role, goal, tools, and Human Gate specification
- **§5 Human Gate Policy** — Brand Profile Approval gate definition: when it fires, what the user reviews, what happens next
- **§6 Brand Profile Schema** — The exact JSON structure Agent 1 must validate, enrich, and output
- **§3.6 Crew I/O Contracts** — DS Bootstrap Crew writes `brand-profile.json` (validated); all downstream crews read it
- **§3.7 Model Assignment Strategy** — Agent 1 is Tier 2 (Claude Sonnet): analytical work, not generative
- **§13.3 Validation and Error Handling** — defines what the CLI validates vs. what is deferred to Agent 1
- **§13.5 Non-interactive Mode** — `--profile` mode also routes through Agent 1 for validation/enrichment

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — establishes the validated `brand-profile.json` written by Bootstrap and consumed by all downstream crews
- [ ] Retry protocol (§3.4)
- [x] Human gate policy (§5) — implements Gate 1 (Brand Profile Approval)
- [ ] Exit criteria (§8)
- [x] Brand Profile schema (§6) — first time the §6 schema is enforced in code, not just in spec

## Approach

1. **Define Brand Profile JSON Schema** — translate the §6 schema into a machine-validatable JSON Schema document; use this as the source of truth for the Validator tool
2. **Implement `ArchetypeResolver` tool** — a data-driven Python class with a hardcoded defaults map per archetype; for `custom`, apply a universal baseline and leave creative fields unconstrained; returns a complete defaults dict that the Default Filler merges into the profile
3. **Implement `ConsistencyChecker` tool** — rule list checked in order; each rule is a predicate on the profile dict + a human-readable error message; returns a list of `{ field, message, severity }` objects; `error` severity blocks; `warning` continues with a logged note
4. **Implement `DefaultFiller` tool** — iterates over `archetype_defaults[profile.archetype]` and fills any `None` / missing field in the profile; returns the merged, complete profile
5. **Implement `BrandProfileValidator` tool** — runs JSON Schema validation; returns structured errors with field paths
6. **Define `BrandDiscoveryAgent`** — CrewAI `Agent(role=..., goal=..., backstory=..., tools=[...], llm=tier2_model)`; task T1 receives the raw profile, runs all four tools in sequence, and returns the enriched profile as structured output
7. **Implement Human Gate prompt** — after Agent 1 completes, print the enriched profile as a formatted summary (not raw JSON) and prompt: `"Approve this brand profile and start generation? [y/N]"`; on `y` → write final `brand-profile.json` and exit with code 0; on `N` → inform user to re-run `daf init`, exit with code 1
8. **Wire `daf generate` command** — add `generate` subcommand to `cli.py`; loads `brand-profile.json` from cwd or `--profile` flag, invokes Agent 1 task, runs the gate prompt
9. **Unit tests** — test each tool with valid and invalid inputs; test gate prompt with `y` and `N` responses; test full flow with a fixture `brand-profile.json`

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| CrewAI task output format is unstructured (free text instead of JSON) | Medium | Use `output_json=BrandProfileModel` on the CrewAI Task to enforce structured output; Pydantic model mirrors the §6 schema |
| Consistency rule set grows complex and hard to maintain | Low | Keep rules as a flat list of `(predicate, message)` tuples; add new rules without touching existing ones |
| Agent 1 model (Sonnet) hallucinates new fields not in §6 schema | Low | Pydantic output model enforces the schema contract; extra fields are stripped |
| Human Gate prompt blocks CI/CD usage | Low | `daf generate --yes` flag skips the approval prompt (auto-approves); document that CI/CD should use `--yes` with a pre-validated `--profile` |
