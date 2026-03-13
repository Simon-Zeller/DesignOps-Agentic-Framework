# Design: p10-token-engine-crew

## Technical Approach

The Token Engine Crew replaces its no-op stub with a real CrewAI `Crew` sequencing five agents (7–11) across tasks T1→T5. Each agent is a thin decision layer that invokes deterministic tools; no agent performs data transformation directly. The crew reads raw token files from `tokens/` (written by Phase 1's Token Foundation Agent) and writes validated, compiled outputs to `tokens/compiled/` and `tokens/diff.json`.

The implementation follows the same structural pattern as existing agents in `src/daf/agents/`: an `Agent` factory function and a `Task` factory function, both living in a single module. The crew factory in `src/daf/crews/token_engine.py` is replaced entirely — the stub is removed and a real `Crew` instance is assembled from the five tasks.

Eight new deterministic tools are introduced under `src/daf/tools/`. Tools that overlap with existing utilities reuse them: `WC3DTCGFormatter` (normalisation in T1) and `StyleDictionaryCompiler` (compilation in T3) are existing tools; the new tools cover the validation, integrity, and diff capabilities not yet present.

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| DTCG format normalisation | Deterministic | Pure structural transformation; no ambiguity |
| Duplicate / naming conflict detection | Deterministic | String matching and key-set comparison |
| W3C DTCG schema validation | Deterministic | JSON Schema validation against pinned spec |
| Naming convention enforcement | Agent (interpretation) + Deterministic (rule check) | Linter produces violations; Agent interprets severity and suggests fixes |
| WCAG contrast calculation | Deterministic | Mathematical formula: `contrast_safe_pairer.py` already exists |
| Style Dictionary compilation | Deterministic | Tool invocation; Agent decides platforms and theme list |
| Per-theme CSS file generation | Deterministic | Template expansion from `$extensions.com.daf.themes` values |
| Cross-tier reference graph traversal | Deterministic | Graph walk across three loaded JSON files |
| Circular reference detection | Deterministic | DFS cycle detection on the reference graph |
| Orphan token detection | Deterministic | Set difference: defined tokens minus referenced tokens |
| Phantom reference detection | Deterministic | Reference targets checked against the full key set |
| Tier-skip violation detection | Deterministic | Edge classification in reference graph |
| Token diff generation | Deterministic | Key-set comparison between prior and current token sets |
| Deprecation tagging | Deterministic | `$extensions.com.daf.deprecated` injection by rule |
| Deciding whether validation failure triggers retry vs. skip | Agent | Requires reasoning about severity, category, and downstream impact |
| Structuring rejection context for Agent 6 | Agent | Synthesises multiple tool outputs into a coherent, actionable rejection message |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Agent 7: Token Ingestion Agent | Tier 3 | Haiku | Structured I/O; normalisation is deterministic; minimal ambiguity |
| Agent 8: Token Validation Agent | Tier 2 | Sonnet | Must interpret naming violations, decide severity, synthesise rejection context for retry |
| Agent 9: Token Compilation Agent | Tier 3 | Haiku | Invokes compiler with known parameters; no interpretive reasoning required |
| Agent 10: Token Integrity Agent | Tier 2 | Sonnet | Interprets graph anomalies (orphans vs. dead code vs. genuine errors), decides which violations are fatal |
| Agent 11: Token Diff Agent | Tier 3 | Haiku | Structured comparison and JSON serialisation; no ambiguity |

## Architecture Decisions

### Decision: Rejection file as cross-phase retry contract

**Context:** Agent 6 (First Publish Agent, p09) must detect Token Engine failures and re-invoke Agent 2 (Token Foundation Agent) with structured rejection context. The retry mechanism requires a machine-readable representation of what failed and why, stable across changes.

**Decision:** Agent 8 writes `tokens/validation-rejection.json` on validation failure. The schema is:
```json
{
  "phase": "token-validation",
  "agent": 8,
  "attempt": 1,
  "timestamp": "ISO-8601",
  "failures": [
    {
      "check": "naming_convention | dtcg_schema | wcag_contrast | reference_integrity",
      "severity": "fatal | warning",
      "token_path": "color.brand.primary",
      "detail": "...",
      "suggestion": "..."
    }
  ],
  "fatal_count": 3,
  "warning_count": 1
}
```
Agent 6 reads this file after the Token Engine Crew exits non-zero. Only `fatal_count > 0` triggers a retry.

**Consequences:** Agent 6 from p09 requires a minor update to read `tokens/validation-rejection.json` and extract the failures array for Agent 2's retry context. The file is deleted on successful validation to prevent stale rejections from being misread on subsequent runs.

### Decision: Reference graph loaded across all three tier files simultaneously

**Context:** The `$value` reference syntax (`{tier.category.name}`) can span files — a semantic token in `semantic.tokens.json` references a global token in `base.tokens.json`. A single-file walker cannot resolve cross-file references.

**Decision:** `reference_graph_walker.py` loads all three tier files into a single merged key namespace before walking. The loader prefixes keys with their tier identifier if keys conflict, and the graph walk resolves references within this merged namespace. Tier-skip violations are detected by inspecting which tier a reference source belongs to vs. its target tier.

**Consequences:** All three files must be present and loadable simultaneously. If any tier file is missing, the integrity check fails fast (Fatal, not Warning). The merge strategy uses insertion order: component > semantic > global for conflict resolution (component-scoped definitions take precedence).

### Decision: Style Dictionary invoked from the existing `style_dictionary_compiler.py` tool

**Context:** `src/daf/tools/style_dictionary_compiler.py` already exists from an earlier change. Agent 9 needs per-theme CSS output, which requires extending the existing tool rather than duplicating it.

**Decision:** Extend `StyleDictionaryCompiler` with a `compile_themes(token_dir, output_dir, themes)` method that iterates over the themes list from the Brand Profile and produces one CSS file per theme. The existing `compile()` method is preserved unchanged for backward compatibility.

**Consequences:** The existing `test_token_compilation_strategy.py` test suite continues to pass. New tests cover the `compile_themes` path. The Theme Resolver utility (`theme_utils.py`, already present) is used to expand `$extensions.com.daf.themes` values into per-theme token snapshots before compilation.

### Decision: Fake diff for initial generation (no prior version)

**Context:** `json_diff_engine.py` compares a prior and current token set. On initial generation, no prior version exists.

**Decision:** When no prior `tokens/diff.json` and no prior compiled tokens are found, Agent 11 treats the current token set as the prior (empty), making every token an `added` entry. This produces a full inventory diff — consistent with PRD §4.2 ("all tokens are classified as `added`") — and feeds the Documentation Crew a structured token catalog regardless of whether this is an initial generation or re-generation.

**Consequences:** `json_diff_engine.py` accepts `prior: dict | None` as a parameter. When `None`, it returns a diff with every key classified as `added`.

## Data Flow

```
[DS Bootstrap Crew — Phase 1]
  Agent 2 (Token Foundation)
  ──writes──► tokens/base.tokens.json
  ──writes──► tokens/semantic.tokens.json
  ──writes──► tokens/component.tokens.json

[Token Engine Crew — Phase 2]
  Agent 7 (Ingestion):    reads  tokens/*.tokens.json
                          writes tokens/staged/*.tokens.json   (normalised)
  Agent 8 (Validation):   reads  tokens/staged/*.tokens.json
                          writes tokens/validation-rejection.json  (on failure)
  Agent 9 (Compilation):  reads  tokens/staged/*.tokens.json
                          writes tokens/compiled/variables.css
                          writes tokens/compiled/variables-{theme}.css (per theme)
                          writes tokens/compiled/variables.scss
                          writes tokens/compiled/tokens.ts
                          writes tokens/compiled/tokens.json
  Agent 10 (Integrity):   reads  tokens/staged/*.tokens.json
                          writes tokens/integrity-report.json
  Agent 11 (Diff):        reads  tokens/staged/*.tokens.json
                          reads  tokens/diff.json (prior, optional)
                          writes tokens/diff.json

[Downstream Consumers]
  Design-to-Code Crew     ──reads──► tokens/compiled/tokens.ts
                                     tokens/compiled/tokens.json
  Component Factory Crew  ──reads──► tokens/compiled/tokens.json
  Documentation Crew      ──reads──► tokens/diff.json
  Analytics Crew          ──reads──► tokens/compiled/**, tokens/diff.json

[Cross-phase retry — Agent 6 mediates]
  Agent 8 failure ──(validation-rejection.json)──► Agent 6
  Agent 6         ──(rejection context)──► Agent 2 (re-run Phase 1 agent)
  Agent 2 output  ──(new token files)──► Token Engine Crew (re-run Phase 2)
```

## Retry & Failure Behavior

**Retry boundary:** Token Validation Agent (8) ↔ Token Foundation Agent (2), §3.4.

1. Agent 8 detects fatal validation failures (DTCG schema violation, naming violation, WCAG contrast failure).
2. Agent 8 writes `tokens/validation-rejection.json` with structured failure context.
3. Token Engine Crew exits non-zero; Agent 6 reads the rejection file.
4. Agent 6 re-invokes Agent 2's task with the failures array appended to the original task description (accumulating retry context: attempt N sees all prior rejections).
5. Agent 2 rewrites `tokens/*.tokens.json`.
6. Agent 6 re-runs the full Token Engine Crew.
7. Maximum 3 retry attempts (§3.4). On exhaustion: token set is marked `failed` in `reports/generation-summary.json`; checkpoint is preserved; pipeline continues to Phase 3 with last-best-attempt tokens (warned, not fatal to pipeline).

**Warning-only failures (Agent 10):**
- Orphaned tokens → `integrity-report.json`, Warning severity, no retry triggered.
- Deprecated tokens → `integrity-report.json`, Warning severity.
- Fatal integrity failures (circular reference, phantom reference, tier-skip) → written to `validation-rejection.json` alongside Agent 8 failures; counted as fatal for retry decision.

**Compilation failure (Agent 9):**
- Style Dictionary errors (e.g., unresolvable reference in compiled output) → Agent 9 re-throws; Token Engine Crew exits non-zero; Agent 6 triggers retry using the compilation error as rejection context.

## File Changes

**New files:**
- `src/daf/agents/token_ingestion.py` (new) — Agent 7: Token Ingestion Agent
- `src/daf/agents/token_validation.py` (new) — Agent 8: Token Validation Agent
- `src/daf/agents/token_compilation.py` (new) — Agent 9: Token Compilation Agent
- `src/daf/agents/token_integrity.py` (new) — Agent 10: Token Integrity Agent
- `src/daf/agents/token_diff.py` (new) — Agent 11: Token Diff Agent
- `src/daf/tools/dtcg_schema_validator.py` (new) — DTCG JSON Schema validation tool
- `src/daf/tools/naming_linter.py` (new) — token naming convention enforcer
- `src/daf/tools/reference_graph_walker.py` (new) — cross-tier reference graph traversal
- `src/daf/tools/circular_ref_detector.py` (new) — DFS cycle detection
- `src/daf/tools/orphan_scanner.py` (new) — unused token detector
- `src/daf/tools/phantom_ref_scanner.py` (new) — missing-reference detector
- `src/daf/tools/json_diff_engine.py` (new) — structured token diff generator
- `src/daf/tools/deprecation_tagger.py` (new) — `$extensions.com.daf.deprecated` injector
- `tests/test_token_ingestion_agent.py` (new) — Agent 7 unit tests
- `tests/test_token_validation_agent.py` (new) — Agent 8 unit tests
- `tests/test_token_compilation_agent.py` (new) — Agent 9 unit tests
- `tests/test_token_integrity_agent.py` (new) — Agent 10 unit tests
- `tests/test_token_diff_agent.py` (new) — Agent 11 unit tests
- `tests/test_dtcg_schema_validator.py` (new) — schema validator tool tests
- `tests/test_naming_linter.py` (new) — naming linter tool tests
- `tests/test_reference_graph_walker.py` (new) — graph walker tool tests
- `tests/test_circular_ref_detector.py` (new) — cycle detector tool tests
- `tests/test_orphan_scanner.py` (new) — orphan scanner tool tests
- `tests/test_phantom_ref_scanner.py` (new) — phantom ref scanner tool tests
- `tests/test_json_diff_engine.py` (new) — diff engine tool tests
- `tests/test_deprecation_tagger.py` (new) — deprecation tagger tool tests
- `tests/test_token_engine_crew.py` (new) — integration test for full crew flow

**Modified files:**
- `src/daf/crews/token_engine.py` (modified) — replace stub with real Crew; rename `StubCrew` import to real `Crew` import
- `src/daf/tools/style_dictionary_compiler.py` (modified) — add `compile_themes()` method for per-theme CSS output
- `src/daf/agents/__init__.py` (modified) — export the five new agent factory functions
