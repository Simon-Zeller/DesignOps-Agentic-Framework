# Specification

## Purpose

Defines the behavioral requirements for the unified Exit Criteria evaluation system (PRD §8). This spec covers the `ExitCriteriaEvaluator` tool, the `ExitCriteriaAgent` (Agent 30-bis), the Governance Crew task extension, and the Release Crew `final_status` update.

All 15 PRD §8 criteria are specified as verifiable requirements with Given/When/Then scenarios and acceptance criteria.

---

## Requirements

### Requirement: EX-01 — ExitCriteriaEvaluator runs all 15 §8 checks

The `ExitCriteriaEvaluator` tool MUST evaluate all 15 exit criteria defined in PRD §8 when invoked with an output directory path. It MUST classify each criterion as `fatal` or `warning` per the PRD table. It MUST produce a `reports/exit-criteria.json` file at the output directory root.

#### Acceptance Criteria

- [ ] `ExitCriteriaEvaluator._run(output_dir=<path>)` returns a dict with keys `criteria` (list of 15 items) and `isComplete` (bool)
- [ ] Each item in `criteria` has: `id` (int 1–15), `description` (str), `severity` (`"fatal"` | `"warning"`), `passed` (bool), `detail` (str)
- [ ] Fatal criteria: IDs 1–8. Warning criteria: IDs 9–15
- [ ] `isComplete` is `True` iff all 8 Fatal criteria have `passed: True`
- [ ] `reports/exit-criteria.json` is written to disk with the same structure

#### Scenario: All 15 criteria pass

- GIVEN an output directory with valid tokens, compiled CSS, zero TypeScript errors, passing npm build, and all Warning files present and valid
- WHEN `ExitCriteriaEvaluator._run(output_dir=<path>)` is called
- THEN all 15 `criteria` items have `passed: True`
- AND `isComplete` is `True`
- AND `reports/exit-criteria.json` contains `"isComplete": true`

#### Scenario: One Fatal criterion fails

- GIVEN an output directory where `tokens/*.tokens.json` contains a malformed JSON file (C1 fails)
- WHEN `ExitCriteriaEvaluator._run(output_dir=<path>)` is called
- THEN criterion ID 1 has `passed: False` and a non-empty `detail` string
- AND `isComplete` is `False`
- AND all other criteria that can be evaluated are still evaluated

#### Scenario: Only Warning criteria fail

- GIVEN an output directory where all 8 Fatal criteria pass but C9 (unit tests) shows failures
- WHEN `ExitCriteriaEvaluator._run(output_dir=<path>)` is called
- THEN criterion ID 9 has `passed: False` and severity `"warning"`
- AND `isComplete` is `True`

---

### Requirement: EX-02 — C1 Token JSON parses without error (Fatal)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST attempt `json.loads` on every `*.tokens.json` file under `tokens/` in the output directory. If any file fails to parse, criterion 1 MUST be `passed: False`.

#### Acceptance Criteria

- [ ] When `tokens/*.tokens.json` files all parse successfully, C1 is `passed: True`
- [ ] When any `*.tokens.json` file contains invalid JSON, C1 is `passed: False` with `detail` containing the file path and parse error
- [ ] When `tokens/` directory is absent, C1 is `passed: False` with `detail: "tokens/ directory not found"`

#### Scenario: Valid token files

- GIVEN a `tokens/` directory with two valid JSON files
- WHEN C1 is evaluated
- THEN `passed: True` and `detail: ""`

#### Scenario: Invalid JSON in one token file

- GIVEN a `tokens/` directory containing a file with a JSON syntax error
- WHEN C1 is evaluated
- THEN `passed: False` and `detail` names the offending file

---

### Requirement: EX-03 — C2 Token JSON conforms to W3C DTCG schema (Fatal)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST invoke `DtcgSchemaValidator` on the merged token object. Criterion 2 MUST be `passed: False` when `DtcgSchemaValidator` returns a non-empty `fatal` list.

#### Acceptance Criteria

- [ ] When `DtcgSchemaValidator` returns `{"fatal": [], "warnings": [...]}`, C2 is `passed: True`
- [ ] When `DtcgSchemaValidator` returns `{"fatal": ["<error>"], ...}`, C2 is `passed: False` with `detail` listing the fatal errors
- [ ] When token files are absent (C1 already failed), C2 is `passed: False` with `detail: "token files unavailable"`

---

### Requirement: EX-04 — C3 & C4 Token reference resolution (Fatal)

Affects: Governance Crew, Agent 30-bis (all token scope tiers: global, semantic, component-scoped). The evaluator MUST invoke `TokenGraphTraverser` to check that all `{curly.brace}` references in semantic tokens resolve to global tokens (C3), and all component-scoped token references resolve to semantic tokens (C4). Any unresolved reference MUST set the criterion to `passed: False`.

#### Acceptance Criteria

- [ ] C3 is `passed: True` when `TokenGraphTraverser` returns `{"unresolved_refs": []}`
- [ ] C3 is `passed: False` when `unresolved_refs` is non-empty, with `detail` listing unresolved paths
- [ ] C4 applies the same logic for component-scoped token files
- [ ] Both C3 and C4 are `passed: False` with appropriate `detail` when token files are absent

---

### Requirement: EX-05 — C5 WCAG contrast check (Fatal, WCAG AA)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST invoke `ContrastSafePairer` on the semantic token layer. Criterion 5 MUST be `passed: False` when `all_pass` is `False`. The target WCAG level is AA (4.5:1 for normal text, per PRD §8).

#### Acceptance Criteria

- [ ] When `ContrastSafePairer` returns `{"all_pass": True, ...}`, C5 is `passed: True`
- [ ] When `ContrastSafePairer` returns `{"all_pass": False, "pairs": [...]}`, C5 is `passed: False` with `detail` summarising failing pairs
- [ ] Missing semantic token layer results in `passed: False`

---

### Requirement: EX-06 — C6 CSS custom properties have no undefined references (Fatal)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST invoke `TokenRefChecker.check_token_refs` against the compiled CSS output. Criterion 6 MUST be `passed: False` when `all_resolved` is `False`.

#### Acceptance Criteria

- [ ] When all CSS token references resolve, C6 is `passed: True`
- [ ] When any CSS token reference is unresolved, C6 is `passed: False` with `detail` listing unresolved references
- [ ] When compiled CSS is absent, C6 is `passed: False`

---

### Requirement: EX-07 — C7 TypeScript compiles with zero errors (Fatal)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST run `tsc --noEmit` as a subprocess in the generated package directory. Criterion 7 MUST be `passed: False` when the tsc exit code is non-zero.

#### Acceptance Criteria

- [ ] When `tsc --noEmit` exits 0, C7 is `passed: True`
- [ ] When `tsc --noEmit` exits non-zero, C7 is `passed: False` with `detail` containing the first 500 characters of stderr
- [ ] When `tsc` is not installed or the package directory is absent, C7 is `passed: False` with an informative `detail`
- [ ] In unit tests, the subprocess call is mocked (no real tsc invocation)

---

### Requirement: EX-08 — C8 npm install and build complete without errors (Fatal)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST invoke `DependencyResolver` to run `npm install && npm run build`. Criterion 8 MUST be `passed: False` when `DependencyResolver` returns `{"success": False}`.

#### Acceptance Criteria

- [ ] When `DependencyResolver` returns `{"success": True, "errors": []}`, C8 is `passed: True`
- [ ] When `DependencyResolver` returns `{"success": False, "errors": [...]}`, C8 is `passed: False` with `detail` from `errors`
- [ ] In unit tests, `DependencyResolver` is mocked

---

### Requirement: EX-09 — C9 All unit tests pass (Warning)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST read `reports/generation-summary.json` and check the `test_results.all_pass` field. Criterion 9 MUST be `passed: False` when `all_pass` is `False` or the field is absent.

#### Acceptance Criteria

- [ ] C9 is `passed: True` when `test_results.all_pass` is `True`
- [ ] C9 is `passed: False` with severity `"warning"` when `all_pass` is `False`
- [ ] C9 is `passed: False` when `reports/generation-summary.json` is absent

---

### Requirement: EX-10 — C10 No hardcoded color/spacing values in source (Warning)

Affects: Governance Crew, Agent 30-bis. All output scope tiers (Starter/Standard/Comprehensive). The evaluator MUST invoke `AstPatternMatcher` and check for `type == "hardcoded_color"` targets. Criterion 10 MUST be `passed: False` when any hardcoded color is found.

#### Acceptance Criteria

- [ ] C10 is `passed: True` when `AstPatternMatcher` returns `{"targets": []}`
- [ ] C10 is `passed: False` with severity `"warning"` when any `target.type` is `"hardcoded_color"`
- [ ] C10 is `passed: True` when the `src/` directory is absent (no generated components to scan)

---

### Requirement: EX-11 — C11 All interactive components have ARIA roles (Warning, WCAG AA)

Affects: Governance Crew, Agent 30-bis. All output scope tiers. The evaluator MUST invoke `A11yAttributeExtractor.extract_a11y_attributes` for all interactive components in the component registry. Criterion 11 MUST be `passed: False` when any component lacks a required ARIA role attribute.

#### Acceptance Criteria

- [ ] C11 is `passed: True` when all interactive components in registry have ARIA roles declared in their spec
- [ ] C11 is `passed: False` with severity `"warning"` when any interactive component is missing a required ARIA attribute
- [ ] C11 evaluates against the WCAG AA criterion 4.1.2 (Name, Role, Value)

---

### Requirement: EX-12 — C12 All components score ≥70/100 on quality gate (Warning)

Affects: Governance Crew, Agent 30-bis. All output scope tiers. The evaluator MUST read `reports/governance/quality-gates.json` via `GateStatusReader`. Criterion 12 MUST be `passed: False` when any component has a composite score below 70.

#### Acceptance Criteria

- [ ] C12 is `passed: True` when all components in `quality-gates.json` have `score >= 70`
- [ ] C12 is `passed: False` with severity `"warning"` when any component has `score < 70`
- [ ] C12 is `passed: False` when `reports/governance/quality-gates.json` is absent

---

### Requirement: EX-13 — C13 Spec ↔ code ↔ docs consistency check passes (Warning)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST read `reports/governance/drift-report.json`. Criterion 13 MUST be `passed: False` when the report contains any item with `category == "re-run-required"` or the `non_fixable` list is non-empty.

#### Acceptance Criteria

- [ ] C13 is `passed: True` when `non_fixable` is empty
- [ ] C13 is `passed: False` with severity `"warning"` when `non_fixable` is non-empty
- [ ] C13 is `passed: False` when `reports/governance/drift-report.json` is absent

---

### Requirement: EX-14 — C14 Component registry JSON is valid and complete (Warning)

Affects: Governance Crew, Agent 30-bis. The evaluator MUST read `reports/component-registry.json` and validate it with `JsonSchemaValidator` against the registry JSON schema. Criterion 14 MUST be `passed: False` when validation returns `{"valid": False}` or the file is absent.

#### Acceptance Criteria

- [ ] C14 is `passed: True` when `validate_spec_schema` returns `{"valid": True, ...}`
- [ ] C14 is `passed: False` with severity `"warning"` when validation returns errors
- [ ] C14 is `passed: False` when `reports/component-registry.json` is absent

---

### Requirement: EX-15 — C15 No components marked `failed` in generation summary (Warning)

Affects: Governance Crew, Agent 30-bis. All output scope tiers. The evaluator MUST read `reports/generation-summary.json` and check that no component entry has `status == "failed"`. Criterion 15 MUST be `passed: False` when any failed component is found.

#### Acceptance Criteria

- [ ] C15 is `passed: True` when `generation-summary.json` has no `status: "failed"` entries
- [ ] C15 is `passed: False` with severity `"warning"` when any component has `status: "failed"`
- [ ] C15 is `passed: False` when `reports/generation-summary.json` is absent

---

### Requirement: EX-16 — ExitCriteriaAgent (Agent 30-bis) factory

Affects: Governance Crew. A factory function `create_exit_criteria_agent(model, output_dir)` MUST return a `crewai.Agent` with role `"Exit Criteria Evaluator"`, using `ExitCriteriaEvaluator` and `ReportWriter` as tools, assigned to the Haiku model tier.

#### Acceptance Criteria

- [ ] `create_exit_criteria_agent(model, output_dir)` returns a `crewai.Agent` instance
- [ ] The agent has exactly two tools: `ExitCriteriaEvaluator` and `ReportWriter`
- [ ] The agent is documented with a descriptive backstory referencing PRD §8

---

### Requirement: EX-17 — Governance Crew wires t5_exit_criteria after t4_quality_gate

Affects: Governance Crew (Agent 30-bis). The `create_governance_crew(model, output_dir)` factory MUST include a `t5_exit_criteria` Task after `t4_quality_gate` in the sequential task list. The task's expected output MUST be `reports/exit-criteria.json`.

#### Acceptance Criteria

- [ ] `create_governance_crew(...)` includes `t5_exit_criteria` in the task list
- [ ] `t5_exit_criteria` appears after `t4_quality_gate` in task ordering
- [ ] The task description references the output directory and `reports/exit-criteria.json`

---

### Requirement: EX-18 — Release Crew t6_final_status reads exit-criteria.json

Affects: Release Crew, Agent 39 – Publish Agent. The `t6_final_status` task description MUST instruct the agent to read `reports/exit-criteria.json` and map `isComplete` to `final_status`:

- `isComplete: true` → `final_status: "success"` (if no warnings) OR `"partial"` (if any Warning criteria failed)
- `isComplete: false` → `final_status: "failed"`

#### Acceptance Criteria

- [ ] `t6_final_status` task description references `reports/exit-criteria.json` as its input
- [ ] Task description defines the three-way mapping: `success`, `partial`, `failed`
- [ ] `reports/generation-summary.json` is updated with the mapped `final_status` value
