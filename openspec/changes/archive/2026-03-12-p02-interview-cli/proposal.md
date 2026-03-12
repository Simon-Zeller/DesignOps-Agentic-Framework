# Proposal: p02-interview-cli

## Intent

The `daf init` command exists as a stub (P01) but has no interview logic. Until a user can actually answer brand questions and produce a `brand-profile.json`, the pipeline cannot start. This is the user-facing entry point to the entire DAF system — without it, the product has no meaningful input path.

P02 implements the 11-step brand interview specified in §13, producing a raw `brand-profile.json` that seeds the DS Bootstrap Crew. It is the only interactive component in the entire pipeline — everything downstream is autonomous.

## Scope

### In scope

- 11-step sequential interview flow in the terminal (§13.2)
- Archetype-derived defaults shown at each optional step — accept with Enter, or override
- Color input accepting hex values (`#1a73e8`) and natural language descriptions
- Basic structural validation before writing output (§13.3): required fields, hex validity, scale ratio bounds, base size bounds, archetype enum
- Session persistence via `.daf-session.json` after each step — resume on re-run if interrupted (§13.3)
- Output: raw `brand-profile.json` conforming to the §6 schema, written to the current directory
- Non-interactive bypass: `daf init --profile <path>` passes an existing profile directly to the next stage, skipping the interview (§13.5)
- Clean UX: progress indicators, step numbering, inline defaults, clear prompts

### Out of scope

- Semantic validation, contradiction detection, enrichment — deferred to Brand Discovery Agent (Agent 1, P03)
- The Human Gate (brand profile approval prompt) — P03
- Passing `brand-profile.json` to Agent 1 and triggering the pipeline — P03
- Resume-from-checkpoint logic (`--resume` flag behavior) — P08
- Multi-brand `brands[]` configuration beyond basic capture — P10
- CI/CD integration beyond `--profile` flag passthrough

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap (Crew 1) | Agent 1: Brand Discovery Agent | This change produces Agent 1's input: the raw `brand-profile.json`. No agent code changes — only the data contract is established. |

No agent or crew code is implemented here. The interview CLI operates outside CrewAI's task execution model (§4.1) — it is a pure Python CLI that writes a file.

## PRD References

- **§13 Interview CLI Specification** — Primary spec. Defines invocation modes, 11-step flow, validation rules, session persistence, and output contract.
- **§13.1 Invocation** — `daf init`, `daf init --profile`, invocation modes
- **§13.2 Interview Flow** — Step table (steps 1–11), required vs optional, archetype-derived defaults
- **§13.3 Validation and Error Handling** — Structural validation rules, `.daf-session.json` session persistence
- **§13.4 Output** — `brand-profile.json` schema reference
- **§13.5 Non-interactive Mode** — `--profile` flag behavior
- **§6 Brand Profile Schema** — The exact JSON structure this change must produce
- **§4.1 DS Bootstrap Crew** — Pre-pipeline interview CLI description; explains the architectural separation between the CLI and CrewAI agents
- **§5 Human Gate Policy** — Brand Profile Approval gate (triggered after Agent 1 — not implemented here, but contextual)

## Pipeline Impact

- [ ] Pipeline phase ordering
- [ ] Crew I/O contracts (§3.6)
- [ ] Retry protocol (§3.4)
- [ ] Human gate policy (§5)
- [x] Exit criteria (§8)
- [x] Brand Profile schema (§6)

> The interview CLI is the source of `brand-profile.json`. This change establishes the §6 data contract in code for the first time. All downstream phase inputs ultimately trace back to this file. Pipeline flow is unaffected — the interview runs before CrewAI is invoked.

## Approach

1. **Implement archetype defaults map** — a Python dict keyed by archetype (`enterprise-b2b`, `consumer-b2c`, `mobile-first`, `multi-brand`, `custom`) providing default values for each optional §6 field. This is the reference for in-prompt defaults.
2. **Build step-by-step prompt flow** in `src/daf/interview.py` — each of the 11 steps is a function that reads the current session state, displays the prompt with default if applicable, and returns the collected value. Use Typer/Click prompts or `questionary` for multi-choice steps (archetype, density, themes, scope).
3. **Session persistence** — after each step completes, serialize the current answers to `.daf-session.json` in the working directory. On `daf init` with an existing session file, detect it and ask: "Resume from step N?" or "Start over?".
4. **Structural validation** — after step 11, validate the assembled profile against the §13.3 rules before writing. Emit clear field-level errors; let the user re-enter the failing field.
5. **Write `brand-profile.json`** — serialize the validated profile as pretty-printed JSON, delete `.daf-session.json`, and print a confirmation with the output path.
6. **Wire `--profile` flag** — in `cli.py`, if `--profile` is provided, load and minimally validate the file (is it JSON? does it have `name` and `archetype`?), then print confirmation and exit. Full validation remains with Agent 1.
7. **Unit tests** — test each validation rule, archetype default resolution, session save/resume, and `--profile` passthrough.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Natural language color description requires LLM — not available in the CLI | Low | Store raw string as-is; Agent 1 resolves it to hex. The CLI spec explicitly defers intelligence to agents. |
| Session file conflicts in shared directories | Low | Session file is per-directory; document that `daf init` should be run from the intended project output directory |
| `questionary` dependency conflicts with CrewAI pins | Medium | Prefer stdlib `input()` + formatted prompts over `questionary`; use `questionary` only if the UX gain justifies adding the dependency |
| Step 11 (component overrides) is too complex for a terminal prompt | Medium | Offer a simplified prompt: "Add component overrides? (y/N)" — if yes, open `$EDITOR` with a JSON template pre-filled. If editor not available, skip with a note to edit manually. |
