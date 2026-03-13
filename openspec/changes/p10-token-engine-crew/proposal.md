# Proposal: p10-token-engine-crew

## Intent

The pipeline orchestrator (p09) is now implemented: Agent 6 (First Publish Agent) sequences all 9 crews end-to-end. However, the Token Engine Crew — Phase 2 of the pipeline — remains a no-op stub. Its stub writes empty CSS/SCSS/TS/JSON files to satisfy the I/O contract but performs no validation, no naming enforcement, no WCAG contrast checking, no cross-tier reference graph analysis, and no compilation.

This means the tokens produced by the Token Foundation Agent (Agent 2) in Phase 1 are never verified before downstream crews consume them. Any naming violation, broken reference, contrast failure, or tier-skipping error propagates silently into component generation — producing a design system built on invalid tokens with no indication of errors until a much later phase (if at all).

This change delivers the real Token Engine Crew: 5 agents (7–11) that together validate, compile, integrity-check, and diff-document the token set before Phase 3 begins.

## Scope

### In scope

- **Agent 7: Token Ingestion Agent** (`src/daf/agents/token_ingestion.py`) — normalises incoming raw token files to W3C DTCG, detects duplicates and naming conflicts, stages tokens for validation.
- **Agent 8: Token Validation Agent** (`src/daf/agents/token_validation.py`) — validates schema structure, naming conventions, and WCAG contrast ratios for all declared colour pairs.
- **Agent 9: Token Compilation Agent** (`src/daf/agents/token_compilation.py`) — invokes Style Dictionary to compile all configured targets: CSS, SCSS, TypeScript constants, flat JSON, and per-theme CSS files.
- **Agent 10: Token Integrity Agent** (`src/daf/agents/token_integrity.py`) — builds and validates the full cross-tier reference graph; detects tier-skipping, circular refs, orphaned tokens, and phantom references.
- **Agent 11: Token Diff Agent** (`src/daf/agents/token_diff.py`) — generates structured add/modify/remove diffs, writes `tokens/diff.json` for downstream Documentation and Analytics crews.
- **Token Engine Crew factory** (`src/daf/crews/token_engine.py`) — replaces the stub with a real CrewAI `Crew` that sequences tasks T1→T5 using the five agents.
- **New tools** (under `src/daf/tools/`):
  - `dtcg_schema_validator.py` — validates token files against the W3C DTCG JSON Schema.
  - `naming_linter.py` — enforces naming conventions (case, prefix, no abbreviations, tier hierarchy).
  - `reference_graph_walker.py` — traverses `$value` reference chains across all three tier files.
  - `circular_ref_detector.py` — detects cycles in the reference graph.
  - `orphan_scanner.py` — identifies tokens defined but never referenced.
  - `phantom_ref_scanner.py` — identifies tokens that reference non-existent keys.
  - `json_diff_engine.py` — produces structured DTCG-aware diffs (added/modified/removed/deprecated).
  - `deprecation_tagger.py` — tags tokens with `$extensions.com.daf.deprecated` metadata.
- **Token Compilation Strategy** (`src/daf/tools/token_compilation_strategy.py`) — existing file extended to support per-theme CSS output and additional platform targets (Tailwind, Swift XML, Android Compose).
- **Tests** — unit tests for every new tool and agent; integration test for the full Token Engine Crew flow.

### Out of scope

- Generating or modifying token values — the Token Engine Crew is read-validate-compile only; token authoring remains the responsibility of the Token Foundation Agent (2).
- Implementing downstream crews (Design-to-Code, Component Factory, etc.).
- Tailwind, Swift, or Android compiler plugins — foundation only; plugin architecture is in scope, but platform-specific plugins beyond CSS/SCSS/TS/JSON are deferred.
- Real-time token editing or interactive token correction — the retry protocol handles correction via Agent 2.

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| Token Engine | Agent 7: Token Ingestion Agent | **New implementation** — replaces stub task |
| Token Engine | Agent 8: Token Validation Agent | **New implementation** — replaces stub task |
| Token Engine | Agent 9: Token Compilation Agent | **New implementation** — replaces stub task |
| Token Engine | Agent 10: Token Integrity Agent | **New implementation** — replaces stub task |
| Token Engine | Agent 11: Token Diff Agent | **New implementation** — replaces stub task |
| DS Bootstrap | Agent 2: Token Foundation Agent | Integration point — Token Engine picks up `tokens/*.tokens.json` output via I/O contract (§3.6) |
| DS Bootstrap | Agent 6: First Publish Agent | Retry routing — Agent 6 detects Token Validation failures and re-invokes Agent 2 with rejection context (cross-phase retry, §3.4) |
| Design-to-Code | Agents 12–16 | Downstream consumers — they now receive validated, compiled token files instead of stubs |
| Component Factory | Agents 17–20 | Token ref checks now validate against real compiled tokens |
| Documentation | Agents 21–25 | `tokens/diff.json` is now a real structured diff, enabling accurate changelogs |
| Analytics | Agents 36–40 | Token compliance reports operate against real compiled token references |

## PRD References

- §3.1 — Pipeline phases: Phase 2 (Token Engine) position and outputs
- §3.4 — Cross-phase retry routing: Token Validation Agent (8) ↔ Token Foundation Agent (2)
- §3.5 — Theming model: per-theme CSS compilation, `$extensions.com.daf.themes` structure
- §3.6 — Crew I/O contracts: Token Engine inputs (`tokens/*.tokens.json`) and outputs (`tokens/compiled/**`, `tokens/diff.json`)
- §4.2 — Token Engine Crew: all 5 agents (7–11), tasks T1–T5, NFRs
- §8 — Exit criteria: Fatal check F1 (token validity), F2 (DTCG schema), F3 (reference resolution), F4 (WCAG contrast), F5 (CSS reference resolution)

## Pipeline Impact

- [x] Pipeline phase ordering — Token Engine Crew replaces a stub in Phase 2; pipeline sequencing in Agent 6 is unchanged
- [x] Crew I/O contracts (§3.6) — Token Engine now writes fully validated and compiled outputs; downstream crews that previously consumed stub files will now consume real files
- [x] Retry protocol (§3.4) — Agent 8's structured rejection output enables Agent 6 to trigger cross-phase retry back to Agent 2 with specific failure context
- [ ] Human gate policy (§5) — not affected
- [x] Exit criteria (§8) — Fatal checks F1–F5 are directly enabled by this crew; Token Engine's validation agents enforce these gates before Phase 3
- [ ] Brand Profile schema (§6) — not affected

## Approach

1. **New tools first (TDD)** — implement `dtcg_schema_validator`, `naming_linter`, `reference_graph_walker`, `circular_ref_detector`, `orphan_scanner`, `phantom_ref_scanner`, `json_diff_engine`, and `deprecation_tagger`. Each tool is a pure, deterministic function with full unit test coverage before agent wiring.
2. **Extend existing tools** — `style_dictionary_compiler.py` already exists; extend it with per-theme output support and additional platform hooks. `dtcg_formatter.py` is reused by the Ingestion Agent for normalisation.
3. **Five agents** — implement agents 7–11 as CrewAI `Agent` objects with tool bindings. Each agent corresponds to exactly one task in the T1→T5 sequence. Tier-2 (Sonnet) for Validation and Integrity agents (interpretive reasoning); Tier-3 (Haiku) for Ingestion, Compilation, and Diff agents (structured I/O, low ambiguity).
4. **Token Engine Crew factory** — replace the stub in `src/daf/crews/token_engine.py` with a real `Crew` that sequences the five tasks, using `output_dir` to resolve file paths consistent with the §3.6 I/O contract.
5. **Retry integration** — Agent 8 writes a structured rejection to `tokens/validation-rejection.json` when validation fails. Agent 6 reads this file to construct the cross-phase retry context for Agent 2.
6. **Integration test** — an end-to-end test exercises the full Token Engine Crew against a pre-built fixture token set (one valid, one with deliberate DTCG violations). The valid fixture must compile cleanly; the invalid fixture must produce a structured rejection and not advance.

## Risks

- **Style Dictionary version compatibility** — `style_dictionary_compiler.py` targets Style Dictionary v3. Agent 9 must ensure the compiler invocation API has not diverged.
- **DTCG schema evolution** — the W3C DTCG spec is still being finalised. The schema validator should pin to the version used in the rest of the codebase and document the pinned commit.
- **Large token sets and compilation time** — the PRD NFR requires compilation of 5K tokens in <30s. Style Dictionary is synchronous; very large files may exceed this. A streaming/chunked approach may be needed.
- **Cross-tier reference resolution across files** — the Token Integrity Agent must resolve `{tier.category.name}` references across three separate JSON files loaded simultaneously. File loading order matters; a single-pass traversal may produce false phantom-ref errors if forward references are present.
- **Retry rejection format contract** — Agent 6 from p09 reads `tokens/validation-rejection.json` to trigger retries. The schema of this file must be agreed and stable before wiring; a schema mismatch will silently suppress retries.
