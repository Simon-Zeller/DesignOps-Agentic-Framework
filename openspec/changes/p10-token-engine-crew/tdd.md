# TDD Plan: p10-token-engine-crew

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

All tests are written in **pytest** (the existing project test framework). Tools are tested with pure unit tests — no LLM calls, no file system dependencies beyond `tmp_path`. Agent tests use `unittest.mock.patch` to mock CrewAI and LLM invocations; they verify tool composition and task configuration, not LLM output. The integration test exercises the full Token Engine Crew factory against pre-built fixture token sets using a real (temp) directory.

Coverage target: **≥ 80% line coverage** per the PRD quality gate (§8). Branch coverage target: **≥ 70%**.

All tests are written to **fail first** (red phase). Implementation is not started until each test file exists and fails with `NotImplementedError` or `ImportError` on the missing module.

---

## Test Cases

### Token Ingestion Agent (Agent 7)

#### Test: Normalises three valid tier files to staged directory

- **Maps to:** Spec "Token file ingestion and normalisation" → Scenario "Valid three-tier token set"
- **Type:** unit
- **Given:** Three valid DTCG JSON files in a `tmp_path/tokens/` directory
- **When:** `create_token_ingestion_task()` is called and executed with mocked Agent
- **Then:** Three files exist at `tmp_path/tokens/staged/*.tokens.json`
- **File:** `tests/test_token_ingestion_agent.py`

#### Test: Raises on missing tier file

- **Maps to:** Spec "Token file ingestion and normalisation" → Scenario "Missing tier file"
- **Type:** unit
- **Given:** Only `base.tokens.json` and `component.tokens.json` present; `semantic.tokens.json` absent
- **When:** Ingestion task runs
- **Then:** `FileNotFoundError` (or a wrapped CrewAI task failure) is raised; no staged files are written
- **File:** `tests/test_token_ingestion_agent.py`

#### Test: Raises on duplicate key within a tier file

- **Maps to:** Spec "Token file ingestion and normalisation" → Scenario "Duplicate token key within a tier"
- **Type:** unit
- **Given:** `base.tokens.json` contains the same key `color.brand.primary` at two paths (JSON last-write-wins, detected via raw text parse)
- **When:** Ingestion task runs
- **Then:** A `ValueError` is raised with message containing "duplicate" and the conflicting key
- **File:** `tests/test_token_ingestion_agent.py`

---

### DTCG Schema Validator Tool

#### Test: Returns empty violations list for valid DTCG document

- **Maps to:** Spec "DTCG schema compliance validation" → Scenario "Fully DTCG-compliant staged tokens"
- **Type:** unit
- **Given:** A valid DTCG token dict with `$type` and `$value` on all leaf nodes
- **When:** `DTCGSchemaValidator().run(token_dict)` is called
- **Then:** Returns `{"fatal": [], "warnings": []}`
- **File:** `tests/test_dtcg_schema_validator.py`

#### Test: Reports fatal for token missing `$type`

- **Maps to:** Spec "DTCG schema compliance validation" → Scenario "Token missing `$type` field"
- **Type:** unit
- **Given:** Token dict with a leaf node that has `$value` but no `$type`
- **When:** `DTCGSchemaValidator().run(token_dict)` is called
- **Then:** Returns at least one entry in `fatal` with the affected token path
- **File:** `tests/test_dtcg_schema_validator.py`

#### Test: Reports warning for unrecognised extra field

- **Maps to:** Spec "DTCG schema compliance validation" → Scenario "Token with only unrecognised extra field"
- **Type:** unit
- **Given:** Token with valid `$type`/`$value` and unknown field `$foo`
- **When:** Validator runs
- **Then:** One entry in `warnings`, none in `fatal`
- **File:** `tests/test_dtcg_schema_validator.py`

---

### Naming Linter Tool

#### Test: Clean names return empty violation list

- **Maps to:** Spec "Token naming convention enforcement" — happy path
- **Type:** unit
- **Given:** Token keys following kebab-case with recognised category prefixes
- **When:** `NamingLinter().run(keys)` is called
- **Then:** Returns `{"fatal": [], "warnings": []}`
- **File:** `tests/test_naming_linter.py`

#### Test: Blocked abbreviation produces warning

- **Maps to:** Spec "Token naming convention enforcement" → Scenario "Token key contains blocked abbreviation"
- **Type:** unit
- **Given:** Key `"color.bg.primary"` where `bg` is in the blocklist
- **When:** Linter runs
- **Then:** One warning entry with `detail` containing `"abbreviation: bg"`
- **File:** `tests/test_naming_linter.py`

#### Test: Wrong casing produces fatal violation

- **Maps to:** Spec "Token naming convention enforcement" → Scenario "Token key uses wrong casing"
- **Type:** unit
- **Given:** Key `"colorBrandPrimary"` (camelCase)
- **When:** Linter runs
- **Then:** One fatal entry for that key
- **File:** `tests/test_naming_linter.py`

---

### Token Validation Agent (Agent 8)

#### Test: Clean staged tokens — no rejection file written

- **Maps to:** Spec "DTCG schema compliance validation" → Scenario "Fully DTCG-compliant staged tokens"
- **Type:** unit
- **Given:** Valid staged tokens in `tmp_path/tokens/staged/`
- **When:** `create_token_validation_task()` runs (tools mocked to return no violations)
- **Then:** `tmp_path/tokens/validation-rejection.json` does not exist
- **File:** `tests/test_token_validation_agent.py`

#### Test: Fatal violation writes rejection file with correct schema

- **Maps to:** Spec "Cross-phase retry rejection contract" → Scenario "Fatal violation exists — Agent 6 retries"
- **Type:** unit
- **Given:** DTCGSchemaValidator returns one fatal violation
- **When:** Validation task runs
- **Then:** `tokens/validation-rejection.json` exists with keys `phase`, `agent`, `attempt`, `timestamp`, `failures`, `fatal_count`, `warning_count`
- **AND:** `fatal_count` equals 1
- **File:** `tests/test_token_validation_agent.py`

#### Test: Prior rejection file deleted on clean validation

- **Maps to:** Spec "Cross-phase retry rejection contract" → Scenario "Successful validation — rejection file absent"
- **Type:** unit
- **Given:** A stale `tokens/validation-rejection.json` from a prior run exists; all staged tokens are now valid
- **When:** Validation task runs successfully
- **Then:** `tokens/validation-rejection.json` is deleted
- **File:** `tests/test_token_validation_agent.py`

#### Test: WCAG contrast failure produces fatal violation

- **Maps to:** Spec "WCAG contrast ratio verification" → Scenario "Foreground/background pair fails AA threshold"
- **Type:** unit
- **Given:** Staged semantic tokens declare a pair with contrast ratio 3.2:1; `ContrastSafePairer` is injected with a fixture returning that ratio
- **When:** Validation task runs
- **Then:** One fatal violation with `check: "wcag_contrast"` and detail containing ratio values
- **File:** `tests/test_token_validation_agent.py`

#### Test: No colour pairs — warning emitted not fatal

- **Maps to:** Spec "WCAG contrast ratio verification" → Scenario "No colour pair declarations present"
- **Type:** unit
- **Given:** Staged semantic tokens have no foreground/background pair annotations
- **When:** Validation task runs
- **Then:** One warning with `check: "wcag_contrast"`, `fatal_count: 0`
- **File:** `tests/test_token_validation_agent.py`

---

### Token Compilation Agent (Agent 9)

#### Test: Valid staged tokens produce all output files

- **Maps to:** Spec "Multi-platform token compilation" → Scenario "Valid staged tokens compile successfully"
- **Type:** unit (mocked StyleDictionaryCompiler)
- **Given:** Staged tokens in `tmp_path`; `StyleDictionaryCompiler.compile()` is mocked to write fixture output files
- **When:** Compilation task runs
- **Then:** `tokens/compiled/variables.css`, `variables.scss`, `tokens.ts`, `tokens.json` all exist and are non-empty
- **File:** `tests/test_token_compilation_agent.py`

#### Test: Per-theme CSS files generated for each declared theme

- **Maps to:** Spec "Per-theme CSS file generation" → Scenario "Brand Profile declares two themes"
- **Type:** unit (mocked compiler)
- **Given:** Brand Profile with `themes: ["light", "dark"]`, `defaultTheme: "light"`
- **When:** Compilation task runs with mocked `compile_themes()`
- **Then:** `tokens/compiled/variables-light.css` and `tokens/compiled/variables-dark.css` exist
- **AND:** `variables.css` contains light-theme values
- **File:** `tests/test_token_compilation_agent.py`

#### Test: Compiler error propagates as task failure

- **Maps to:** Spec "Multi-platform token compilation" → Scenario "Style Dictionary encounters unresolvable reference"
- **Type:** unit
- **Given:** `StyleDictionaryCompiler.compile()` raises `RuntimeError("unresolvable reference: {color.brand.nonexistent}")`
- **When:** Compilation task runs
- **Then:** The agent re-raises the error; Token Engine Crew exits non-zero
- **File:** `tests/test_token_compilation_agent.py`

#### Test: Missing theme extension falls back to default value

- **Maps to:** Spec "Per-theme CSS file generation" → Scenario "Semantic token missing theme extension for a declared theme"
- **Type:** unit
- **Given:** Token `color.text.default` has no `$extensions.com.daf.themes.dark`; Brand Profile declares `dark` theme
- **When:** Theme resolver runs for dark theme
- **Then:** The token's `$value` is used as fallback; a warning is emitted
- **File:** `tests/test_token_compilation_agent.py`

---

### Reference Graph Walker Tool

#### Test: Flat reference list for simple two-tier graph

- **Maps to:** Spec "Cross-tier reference graph integrity" — happy path
- **Type:** unit
- **Given:** `base.tokens.json` with leaf token `color.brand.primary`; `semantic.tokens.json` with `color.interactive.default` referencing `{color.brand.primary}`
- **When:** `ReferenceGraphWalker().build(base, semantic, component)` is called
- **Then:** Returns a graph with one edge from `color.interactive.default` → `color.brand.primary`
- **File:** `tests/test_reference_graph_walker.py`

#### Test: Detects cross-file reference correctly

- **Maps to:** Design decision "Reference graph loaded across all three tier files simultaneously"
- **Type:** unit
- **Given:** Component token references a semantic token which references a global token
- **When:** Graph walker builds the graph
- **Then:** All three tiers are in the merged namespace; no phantom reference is reported
- **File:** `tests/test_reference_graph_walker.py`

---

### Circular Ref Detector Tool

#### Test: Clean graph returns no cycles

- **Maps to:** Spec "Cross-tier reference graph integrity" → Scenario "Clean reference graph"
- **Type:** unit
- **Given:** Reference graph with no cycles (valid DAG)
- **When:** `CircularRefDetector().detect(graph)` is called
- **Then:** Returns `[]`
- **File:** `tests/test_circular_ref_detector.py`

#### Test: Detects direct cycle A → B → A

- **Maps to:** Spec "Cross-tier reference graph integrity" → Scenario "Circular reference detected"
- **Type:** unit
- **Given:** Graph where token A references B and B references A
- **When:** `CircularRefDetector().detect(graph)` is called
- **Then:** Returns a list with one cycle entry containing the full path `[A, B, A]`
- **File:** `tests/test_circular_ref_detector.py`

---

### Orphan Scanner Tool

#### Test: Referenced token is not flagged as orphan

- **Maps to:** Spec "Cross-tier reference graph integrity" — happy path
- **Type:** unit
- **Given:** Global token `color.brand.primary` is referenced by a semantic token
- **When:** `OrphanScanner().scan(graph)` runs
- **Then:** `color.brand.primary` is NOT in the orphan list
- **File:** `tests/test_orphan_scanner.py`

#### Test: Unreferenced global token flagged as orphan

- **Maps to:** Spec "Cross-tier reference graph integrity" → Scenario "Orphaned global token"
- **Type:** unit
- **Given:** Global token `color.neutral.050` exists but no semantic or component token references it
- **When:** `OrphanScanner().scan(graph)` runs
- **Then:** `color.neutral.050` appears in the orphaned list
- **File:** `tests/test_orphan_scanner.py`

---

### Phantom Ref Scanner Tool

#### Test: Valid references return empty phantom list

- **Type:** unit
- **Given:** All `{reference}` values in all tier files resolve to existing keys in the merged namespace
- **When:** `PhantomRefScanner().scan(merged_namespace, references)` runs
- **Then:** Returns `[]`
- **File:** `tests/test_phantom_ref_scanner.py`

#### Test: Detects missing reference target

- **Maps to:** Spec "Cross-tier reference graph integrity" → Scenario "Phantom reference detected"
- **Type:** unit
- **Given:** Token references `{color.brand.nonexistent}` which does not exist in any tier
- **When:** Scanner runs
- **Then:** Returns one entry with `token_path` and `missing_ref` populated
- **File:** `tests/test_phantom_ref_scanner.py`

---

### Token Integrity Agent (Agent 10)

#### Test: Clean integrity run writes report with zero counts

- **Maps to:** Spec "Integrity report output" → Scenario "Report written on clean run"
- **Type:** unit
- **Given:** All tools mocked to return no violations; valid staged tokens
- **When:** `create_token_integrity_task()` runs
- **Then:** `tokens/integrity-report.json` exists with `fatal_count: 0`, `warning_count: 0`
- **File:** `tests/test_token_integrity_agent.py`

#### Test: Tier-skip violation triggers fatal exit

- **Maps to:** Spec "Cross-tier reference graph integrity" → Scenario "Tier-skip violation detected"
- **Type:** unit
- **Given:** Component token directly references global token (tier-skip); ReferenceGraphWalker returns that violation
- **When:** Integrity task runs
- **Then:** `tokens/validation-rejection.json` is written (or updated) with a `tier_skip` fatal entry
- **AND:** Agent task raises / returns failure status
- **File:** `tests/test_token_integrity_agent.py`

---

### JSON Diff Engine Tool

#### Test: Initial generation classifies all tokens as added

- **Maps to:** Spec "Structured token diff generation" → Scenario "Initial generation — all tokens classified as added"
- **Type:** unit
- **Given:** Current token set with 10 tokens; `prior=None`
- **When:** `JsonDiffEngine().diff(current, prior=None)` is called
- **Then:** All 10 tokens appear in `added[]`; `modified[]`, `removed[]`, `deprecated[]` are empty; `is_initial_generation: True`
- **File:** `tests/test_json_diff_engine.py`

#### Test: Modified token value appears in modified list

- **Maps to:** Spec "Structured token diff generation" → Scenario "Re-generation with modified token"
- **Type:** unit
- **Given:** Prior state has `color.brand.primary: "#005FCC"`; current has `color.brand.primary: "#0066FF"`
- **When:** Diff engine runs
- **Then:** `color.brand.primary` in `modified[]` with correct `old_value` and `new_value`
- **File:** `tests/test_json_diff_engine.py`

#### Test: Removed token appears in removed list

- **Maps to:** Spec "Structured token diff generation" → Scenario "Re-generation with removed token"
- **Type:** unit
- **Given:** Prior state has `color.brand.secondary`; current does not
- **When:** Diff engine runs
- **Then:** `color.brand.secondary` in `removed[]`
- **File:** `tests/test_json_diff_engine.py`

---

### Deprecation Tagger Tool

#### Test: Injects deprecated extension into token

- **Maps to:** Spec "Deprecation tagging" → Scenario "Brand Profile specifies a deprecated token"
- **Type:** unit
- **Given:** Token dict for `color.brand.accent` without `$extensions`; deprecation metadata `{ since: "1.0.0", reason: "..." }`
- **When:** `DeprecationTagger().tag(token_dict, path, metadata)` is called
- **Then:** Token at `color.brand.accent` has `$extensions.com.daf.deprecated: { since: "1.0.0", reason: "..." }`
- **File:** `tests/test_deprecation_tagger.py`

---

### Token Diff Agent (Agent 11)

#### Test: Always writes diff.json on completion

- **Maps to:** Spec "Structured token diff generation" — always-written invariant
- **Type:** unit
- **Given:** Staged tokens in `tmp_path`; `JsonDiffEngine` mocked to return a valid diff
- **When:** `create_token_diff_task()` runs
- **Then:** `tokens/diff.json` exists and is valid JSON
- **File:** `tests/test_token_diff_agent.py`

---

### Style Dictionary Compiler Tool (extended)

#### Test: `compile_themes()` writes one file per theme

- **Maps to:** Spec "Per-theme CSS file generation" → Scenario "Brand Profile declares two themes"
- **Type:** unit
- **Given:** Staged token files in `tmp_path`; themes list `["light", "dark"]`
- **When:** `StyleDictionaryCompiler().compile_themes(token_dir, output_dir, themes)` is called
- **Then:** `output_dir/variables-light.css` and `output_dir/variables-dark.css` are written
- **File:** `tests/test_token_compilation_strategy.py` (extended)

#### Test: Existing `compile()` method is unmodified

- **Maps to:** Design decision "Extend existing compile() method — preserve backward compat"
- **Type:** unit
- **Given:** Existing token compilation strategy tests pass with no changes
- **When:** `StyleDictionaryCompiler().compile()` is called as in prior tests
- **Then:** All existing assertions in `test_token_compilation_strategy.py` still pass
- **File:** `tests/test_token_compilation_strategy.py` (unchanged assertions)

---

### Token Engine Crew Integration

#### Test: Full crew run with valid tokens produces all I/O contract outputs

- **Maps to:** Spec "Multi-platform token compilation" and "Structured token diff generation" — integration
- **Type:** integration
- **Given:** Pre-built fixture with three valid DTCG tier files in `tmp_path/tokens/`; Brand Profile with `themes: ["light", "dark"]`; all agents use mocked LLMs
- **When:** `create_token_engine_crew(str(tmp_path)).run()` is called
- **Then:** All of the following exist and are non-empty:
  - `tokens/staged/base.tokens.json`
  - `tokens/staged/semantic.tokens.json`
  - `tokens/staged/component.tokens.json`
  - `tokens/compiled/variables.css`
  - `tokens/compiled/variables-light.css`
  - `tokens/compiled/variables-dark.css`
  - `tokens/compiled/variables.scss`
  - `tokens/compiled/tokens.ts`
  - `tokens/compiled/tokens.json`
  - `tokens/diff.json`
  - `tokens/integrity-report.json`
- **AND:** `tokens/validation-rejection.json` does NOT exist
- **File:** `tests/test_token_engine_crew.py`

#### Test: Full crew run with invalid tokens writes rejection file and exits non-zero

- **Maps to:** Spec "Cross-phase retry rejection contract" — integration
- **Type:** integration
- **Given:** Fixture token set containing a token missing `$type` (deliberate DTCG violation); mocked LLMs
- **When:** `create_token_engine_crew(str(tmp_path)).run()` is called
- **Then:** Crew exits non-zero
- **AND:** `tokens/validation-rejection.json` exists with `fatal_count >= 1`
- **AND:** `tokens/compiled/` does NOT contain output files (compilation was blocked)
- **File:** `tests/test_token_engine_crew.py`

---

## Edge Case Tests

#### Test: All tokens tagged as deprecated still appear in compiled output

- **Maps to:** Spec "Deprecation tagging" — deprecated tokens are not removed
- **Type:** unit
- **Given:** All tokens in `base.tokens.json` have `$extensions.com.daf.deprecated` injected
- **When:** Compilation task runs
- **Then:** `tokens/compiled/tokens.json` still contains all token keys
- **File:** `tests/test_deprecation_tagger.py`

#### Test: Empty staged token tier file produces fatal error

- **Type:** unit
- **Given:** `tokens/staged/base.tokens.json` is an empty JSON object `{}`
- **When:** Validation task runs
- **Then:** A fatal violation is emitted indicating an empty token tier
- **File:** `tests/test_token_validation_agent.py`

#### Test: Reference graph with all tokens orphaned emits multiple warnings

- **Type:** unit
- **Given:** Three tier files where no semantic token references any global token
- **When:** Orphan scanner runs
- **Then:** All global tokens appear in `integrity-report.json` `warnings[]` with type `"orphan"`
- **AND:** `fatal_count` remains 0
- **File:** `tests/test_orphan_scanner.py`

#### Test: Agent 10 appends to existing rejection file from Agent 8

- **Maps to:** Design decision — integrity violations merge with validation rejection file
- **Type:** unit
- **Given:** A `tokens/validation-rejection.json` already exists from Agent 8 with `fatal_count: 1`; Agent 10 detects a phantom reference
- **When:** Integrity task writes its violations
- **Then:** The rejection file now has `fatal_count: 2` (both violations combined)
- **File:** `tests/test_token_integrity_agent.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥ 80% | PRD quality gate requirement (§8) |
| Branch coverage | ≥ 70% | Covers fatal/warning decision branches in all tools |
| New tool files | 100% branch coverage | Pure deterministic functions; full coverage is achievable |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_token_ingestion_agent.py` | new | Agent 7 unit tests |
| `tests/test_token_validation_agent.py` | new | Agent 8 unit tests (schema, naming, contrast, rejection file) |
| `tests/test_token_compilation_agent.py` | new | Agent 9 unit tests (compilation, per-theme, compiler errors) |
| `tests/test_token_integrity_agent.py` | new | Agent 10 unit tests (graph, tier-skip, orphan, phantom) |
| `tests/test_token_diff_agent.py` | new | Agent 11 unit tests (diff always written) |
| `tests/test_dtcg_schema_validator.py` | new | `DTCGSchemaValidator` tool unit tests |
| `tests/test_naming_linter.py` | new | `NamingLinter` tool unit tests |
| `tests/test_reference_graph_walker.py` | new | `ReferenceGraphWalker` tool unit tests |
| `tests/test_circular_ref_detector.py` | new | `CircularRefDetector` tool unit tests |
| `tests/test_orphan_scanner.py` | new | `OrphanScanner` tool unit tests |
| `tests/test_phantom_ref_scanner.py` | new | `PhantomRefScanner` tool unit tests |
| `tests/test_json_diff_engine.py` | new | `JsonDiffEngine` tool unit tests |
| `tests/test_deprecation_tagger.py` | new | `DeprecationTagger` tool unit tests |
| `tests/test_token_engine_crew.py` | new | Full Token Engine Crew integration test |
| `tests/test_token_compilation_strategy.py` | modified | Add `compile_themes()` tests; existing tests unchanged |
