# Specification

## Purpose

Define the behavioral requirements for the Analytics Crew (Agents 31–35) implementation. This spec covers the five agents, their supporting tools, the crew factory, and the crew-level retry/failure contract as defined in PRD §4.7 and §3.4.

---

## Requirements

### Requirement: Analytics Crew factory replaces stub

The `create_analytics_crew(output_dir)` function in `src/daf/crews/analytics.py` MUST return a `crewai.Crew` instance (not a `StubCrew`), configured with five agents and five tasks wired T1→T2→T3→T4→T5.

#### Acceptance Criteria

- [ ] `create_analytics_crew(output_dir)` returns an instance of `crewai.Crew`
- [ ] The returned crew has exactly 5 agents and 5 tasks
- [ ] Tasks are ordered T1→T5 with `context` chaining
- [ ] The function raises `RuntimeError` if no `*.spec.yaml` files exist in `<output_dir>/specs/`
- [ ] The `reports/` directory is created if it does not exist before any agent runs

#### Scenario: Factory returns a real crew

- GIVEN a valid `output_dir` containing a `specs/` directory with at least one `.spec.yaml` file
- WHEN `create_analytics_crew(output_dir)` is called
- THEN a `crewai.Crew` instance is returned
- AND the crew has 5 agents
- AND the crew has 5 tasks in order T1→T5

#### Scenario: Pre-flight guard fires with missing specs

- GIVEN an `output_dir` whose `specs/` directory is absent or empty
- WHEN `create_analytics_crew(output_dir)` is called
- THEN a `RuntimeError` is raised
- AND the error message references the missing `specs/*.spec.yaml` files

---

### Requirement: Agent 31 – Usage Tracking

Agent 31 (Usage Tracking Agent, Analytics Crew) MUST scan all TSX files in `<output_dir>/src/` to produce a usage-tracking report at `reports/usage-tracking.json`.

Tools used: `ASTImportScanner`, `TokenUsageMapper`, `DependencyGraphBuilder` (existing).

#### Acceptance Criteria

- [ ] `create_usage_tracking_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] The agent is configured with `ASTImportScanner`, `TokenUsageMapper`, and `DependencyGraphBuilder` tools
- [ ] `reports/usage-tracking.json` is written after T1 completes
- [ ] The report identifies tokens referenced in TSX that are not defined in any `tokens/*.tokens.json` (unused or phantom references)
- [ ] The report identifies tokens defined in `tokens/*.tokens.json` but not referenced in any TSX (dead tokens)
- [ ] The report includes per-component import relationships

#### Scenario: All tokens used

- GIVEN a TSX file that references only CSS variables matching keys in `tokens/*.tokens.json`
- WHEN Agent 31 runs T1
- THEN `reports/usage-tracking.json` shows `dead_tokens: []` and `phantom_refs: []`

#### Scenario: Dead token detected

- GIVEN a token key `--color-background-subtle` exists in `tokens/semantic.tokens.json` but is not referenced in any TSX file
- WHEN Agent 31 runs T1
- THEN `reports/usage-tracking.json` contains `"color-background-subtle"` in the `dead_tokens` array

#### Scenario: No TSX files present

- GIVEN `<output_dir>/src/` is empty
- WHEN Agent 31 tool `ASTImportScanner` runs
- THEN it returns an empty result without raising
- AND `reports/usage-tracking.json` is written with empty arrays

---

### Requirement: Agent 32 – Token Compliance

Agent 32 (Token Compliance Agent, Analytics Crew) MUST scan all TSX files for hardcoded style values and deprecated token references, writing `reports/token-compliance.json`.

Tools used: `TokenComplianceScannerTool` (wraps `compute_token_compliance` from `composition_rule_engine`), `TokenUsageMapper`.

#### Acceptance Criteria

- [ ] `create_token_compliance_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] `reports/token-compliance.json` is written after T2 completes and is valid JSON (not `{"stub": true}`)
- [ ] The report contains a `violations` array; each entry MUST include: `file`, `line`, `value`, `type` (one of `color`, `spacing`, `font-size`, `deprecated-token`), and `suggested_token`
- [ ] The report contains a `summary` object with `total_violations`, `by_type` counts, and `compliance_score` (0.0–1.0)
- [ ] `compute_token_compliance` from `composition_rule_engine` is called per file, not re-implemented

#### Scenario: Hardcoded colour violation

- GIVEN a TSX file contains `style={{ color: '#ff0000' }}`
- WHEN Agent 32 runs T2
- THEN `reports/token-compliance.json` `violations` contains an entry with `type: "color"`, `value: "#ff0000"`, and a non-empty `suggested_token`

#### Scenario: Clean file

- GIVEN a TSX file contains only `var(--color-text-primary)` CSS variable references
- WHEN Agent 32 runs T2
- THEN the file contributes zero entries to `violations`
- AND `compliance_score` equals `1.0`

#### Scenario: Deprecated token reference

- GIVEN a TSX file contains a CSS variable `var(--color-text-old)` marked as deprecated in the token set
- WHEN Agent 32 runs T2
- THEN `reports/token-compliance.json` `violations` contains an entry with `type: "deprecated-token"` and the deprecated token name

---

### Requirement: Agent 33 – Drift Detection

Agent 33 (Drift Detection Agent, Analytics Crew) MUST compare canonical spec YAML props against generated TSX props and generated Markdown documentation, classify drift, apply auto-fixable patches, and write `reports/drift-report.json`.

Tools used: `StructuralComparator`, `DriftReporter`, `DocPatcher`.

#### Acceptance Criteria

- [ ] `create_drift_detection_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] `reports/drift-report.json` is written after T3 completes and is valid JSON (not `{"stub": true}`)
- [ ] The report contains `inconsistencies` array; each entry includes: `component`, `source` (spec/code/docs), `description`, `fixable` (bool), `action` (auto-fixed | re-run-required | review)
- [ ] Auto-fixable drift (prop in spec+code but missing from docs) MUST be patched in-place in the Markdown doc
- [ ] Non-fixable drift (prop in spec but missing from code) MUST be flagged with `action: "re-run-required"` and NOT patched
- [ ] Spec is always treated as authoritative over code and docs

#### Scenario: Prop in spec+code, missing from docs

- GIVEN a component spec YAML lists a `disabled` prop
- AND the generated TSX exports a `disabled` prop
- AND the component's Markdown doc does not mention `disabled`
- WHEN Agent 33 runs T3
- THEN the Markdown doc is updated in-place to include the `disabled` prop
- AND `reports/drift-report.json` records this item with `fixable: true, action: "auto-fixed"`

#### Scenario: Prop in spec, missing from code

- GIVEN a component spec YAML lists a `loading` prop
- AND the generated TSX does NOT include a `loading` prop
- WHEN Agent 33 runs T3
- THEN the Markdown doc is NOT modified
- AND `reports/drift-report.json` records this item with `fixable: false, action: "re-run-required"`

#### Scenario: Consistent component

- GIVEN all props in the spec YAML match the TSX props and Markdown props exactly
- WHEN Agent 33 runs T3
- THEN `reports/drift-report.json` `inconsistencies` is empty for that component

---

### Requirement: Agent 34 – Pipeline Completeness

Agent 34 (Pipeline Completeness Agent, Analytics Crew) MUST track each component's completeness across pipeline stages, writing `reports/pipeline-completeness.json`.

Tools used: `PipelineStageTracker`.

Stages checked per component (in order): `spec_validated`, `code_generated`, `a11y_passed`, `tests_written`, `docs_generated`.

#### Acceptance Criteria

- [ ] `create_pipeline_completeness_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] `reports/pipeline-completeness.json` is written after T4 completes
- [ ] Each component entry MUST include: `name`, `stages` (object with boolean per stage), `completeness_score` (0.0–1.0), `stuck_at` (stage name or `null`), `intervention` (string or `null`)
- [ ] A component is considered `stuck_at` the first stage whose boolean is `false`
- [ ] `intervention` MUST be non-null for every component with `stuck_at != null`

#### Scenario: Fully complete component

- GIVEN a component named `Button` has a spec YAML, a TSX file, a test file, a docs Markdown file, and passed accessibility checks
- WHEN Agent 34 runs T4
- THEN `Button`'s entry in `reports/pipeline-completeness.json` shows `completeness_score: 1.0` and `stuck_at: null`

#### Scenario: Component stuck at code generation

- GIVEN a component named `DatePicker` has a spec YAML but no generated TSX file in `src/`
- WHEN Agent 34 runs T4
- THEN `DatePicker`'s entry shows `stuck_at: "code_generated"`, `completeness_score` less than `1.0`, and a non-null `intervention`

#### Scenario: Empty component list

- GIVEN `docs/component-index.json` lists no components
- WHEN Agent 34 runs T4
- THEN `reports/pipeline-completeness.json` is written with an empty `components` array

---

### Requirement: Agent 35 – Breakage Correlation

Agent 35 (Breakage Correlation Agent, Analytics Crew) MUST analyse test failures from the generation pipeline and classify each as `root-cause` or `downstream`, writing `reports/breakage-correlation.json`.

Tools used: `DependencyChainWalker`.

Source of failures: `reports/generation-summary.json` (exhausted-retry failures from Phases 2–3) and `reports/test-results.json` (Release Crew's `npm test` output, if present).

#### Acceptance Criteria

- [ ] `create_breakage_correlation_agent(model, output_dir)` returns a `crewai.Agent`
- [ ] `reports/breakage-correlation.json` is written after T5 completes
- [ ] Each failure entry MUST include: `component`, `failure_type` (test | validation | build), `classification` (root-cause | downstream), `dependency_chain` (ordered list of component names from root to this failure), `root_cause_component` (string or `null` if classification is root-cause)
- [ ] A failure is `root-cause` if its component has no failing dependencies
- [ ] A failure is `downstream` if at least one of its dependency-chain members is also failing

#### Scenario: Root-cause failure

- GIVEN `Button` fails validation with no dependencies
- WHEN Agent 35 runs T5
- THEN `Button`'s entry has `classification: "root-cause"`, `dependency_chain: ["Button"]`, and `root_cause_component: null`

#### Scenario: Downstream failure

- GIVEN `Card` depends on `Button` in `dependency_graph.json`
- AND `Button` is in the failure list
- AND `Card` is also in the failure list
- WHEN Agent 35 runs T5
- THEN `Card`'s entry has `classification: "downstream"`, `dependency_chain` includes `Button`, and `root_cause_component: "Button"`

#### Scenario: No failures present

- GIVEN `reports/generation-summary.json` lists no exhausted-retry failures
- AND `reports/test-results.json` is absent or lists no failures
- WHEN Agent 35 runs T5
- THEN `reports/breakage-correlation.json` is written with `failures: []`

---

### Requirement: Crew-level retry and non-fatal failure

The Analytics Crew MUST conform to the Phase 5 retry policy (PRD §3.4): crew-level retry max 2 attempts; failure is non-fatal.

#### Acceptance Criteria

- [ ] If the crew raises on first attempt, `First Publish Agent (6)` can invoke `create_analytics_crew(output_dir).kickoff()` a second time without error
- [ ] If the crew fails on both attempts, `reports/generation-summary.json` records `analytics: failed` without blocking the Release Crew
- [ ] No individual agent within the crew retries independently

#### Scenario: Crew-level retry on exception

- GIVEN Agent 33 raises a `RuntimeError` during T3 on the first crew run
- WHEN `First Publish Agent` retries the crew
- THEN the crew starts fresh from T1
- AND no partial state from the first run persists (files in `reports/` are overwritten)

#### Scenario: Analytics failure is non-fatal

- GIVEN the Analytics Crew has exhausted both retry attempts
- WHEN `First Publish Agent` evaluates the pipeline result
- THEN the Release Crew still runs
- AND the Output Review gate still opens
