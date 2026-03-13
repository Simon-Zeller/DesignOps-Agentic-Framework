# Specification: RFC Templates & Quality Gate Enforcement

## Purpose

Defines the behavior of Agent 29 (RFC Agent) and Agent 30 (Quality Gate Agent), along with their tools. Agent 29 generates the RFC template and process definition. Agent 30 evaluates all quality gates per component and generates the four TypeScript test suites that encode exit criteria.

## Requirements

### Requirement: RFC template and process definition are generated from workflow structure

Agent 29 MUST generate `docs/templates/rfc-template.md` using `rfc_template_generator.py` and `governance/process.json` using `process_definition_builder.py`. The RFC template MUST document when an RFC is required (new primitive, breaking token change, workflow modification) and the required sections. The process definition MUST encode trigger conditions and approval criteria.

#### Acceptance Criteria

- [ ] `docs/templates/rfc-template.md` exists and contains required sections: Summary, Motivation, Detailed Design, Drawbacks, Alternatives, Adoption Plan.
- [ ] `governance/process.json` contains keys: `rfc_required_for` (list), `approval_criteria` (object), `review_period_days` (int).
- [ ] `rfc_required_for` always includes `"new_primitive"` and `"breaking_token_change"`.
- [ ] `rfc_template_generator.py` produces valid Markdown (non-empty, contains `#` headers).
- [ ] `process_definition_builder.py` returns valid JSON-serializable dict.

#### Scenario: RFC process generation

- GIVEN `governance/workflow.json` is present with standard token and component pipelines
- WHEN Agent 29 runs Task T4
- THEN `governance/process.json` contains `rfc_required_for: ["new_primitive", "breaking_token_change", "workflow_modification"]`
- AND `docs/templates/rfc-template.md` contains the "## Detailed Design" section

#### Scenario: Template is idempotent

- GIVEN Agent 29 runs twice with identical inputs
- WHEN `rfc_template_generator.py` runs on both invocations
- THEN both outputs are byte-for-byte identical
- AND no error is raised on second write (overwrite is safe)

---

### Requirement: Quality Gate Agent evaluates five independent gates per component

Agent 30 MUST evaluate each of the following gates independently for every component. Gates are failures if the condition is not met; they do NOT aggregate into a single score.

| Gate ID | Condition | Data Source |
|---------|-----------|-------------|
| `coverage_80` | Test line coverage ≥ 80% | `reports/quality-scorecard.json` `sub_scores.test_coverage` |
| `a11y_zero_critical` | Zero critical a11y violations | `reports/a11y-audit.json` |
| `no_phantom_refs` | No unresolved token references | `reports/quality-scorecard.json` `phantom_refs` |
| `has_docs` | Component appears in `docs/component-index.json` | `docs/component-index.json` |
| `has_usage_example` | At least one usage example exists in `docs/` | `docs/<ComponentName>/` directory |

The `gate_evaluator.py` tool SHALL accept component name and relevant data sources and return a dict `{"coverage_80": bool, "a11y_zero_critical": bool, "no_phantom_refs": bool, "has_docs": bool, "has_usage_example": bool}` for that component.

#### Acceptance Criteria

- [ ] `governance/quality-gates.json` contains a record for every component.
- [ ] Each record has all five gate IDs as boolean pass (`true`) / fail (`false`).
- [ ] Composite score gate (70/100, from Agent 20) is NOT re-evaluated here — Agent 30 reads Agent 20's result only.
- [ ] `governance/quality-gates.json` is NOT a modification of `reports/quality-scorecard.json`; it is a new, separate file.
- [ ] `gate_evaluator.py` returns all gates as `false` (not as errors) if a required data file is missing.

#### Scenario: Component passes all gates

- GIVEN `Button` has 85% test coverage, zero a11y critical violations, no phantom refs, entry in component-index.json, and a usage example in `docs/Button/`
- WHEN Agent 30 evaluates `Button`
- THEN `governance/quality-gates.json` records all five gates as `true` for `Button`

#### Scenario: Coverage gate fails independently

- GIVEN `Navigation` has composite score `72.0` (above 70 — Agent 20's gate passed) but test coverage `75%` (below 80%)
- WHEN Agent 30 evaluates `Navigation`
- THEN `governance/quality-gates.json` records `coverage_80: false` for `Navigation`
- AND the other four gates are evaluated independently and may still be `true`

#### Scenario: Missing a11y-audit.json

- GIVEN `reports/a11y-audit.json` does not exist for a component
- WHEN `gate_evaluator.py` evaluates `a11y_zero_critical` for that component
- THEN the gate is recorded as `false` (not an exception)
- AND a Warning is logged: `"a11y-audit.json not found for <component>; a11y_zero_critical gate fails"`

---

### Requirement: Test suite generator produces four valid TypeScript test files

Agent 30 MUST generate four TypeScript test files using `test_suite_generator.py`. Each file MUST be syntactically valid TypeScript that Vitest can discover and run. The generator MUST use fixed templates parameterized with actual component names and token paths — no LLM generation.

| File | What it tests |
|------|--------------|
| `tests/tokens.test.ts` | Token JSON validity, DTCG schema conformance, reference resolution |
| `tests/a11y.test.ts` | All interactive components have required ARIA roles |
| `tests/composition.test.ts` | All components compose exclusively from primitives |
| `tests/compliance.test.ts` | No hardcoded color/spacing values in component source |

#### Acceptance Criteria

- [ ] All four files are generated in `tests/` directory when Agent 30 completes Task T5.
- [ ] Each file contains valid TypeScript: `import`, `describe`, `it`/`test` blocks.
- [ ] Component names in the test files match the actual components in the output directory.
- [ ] `test_suite_generator.py` sanitizes component names (remove special chars) before template substitution.
- [ ] Running `tsc --noEmit` on the generated files after TypeScript compilation of the design system produces no syntax errors (type errors from missing imports are acceptable at generation time).
- [ ] Generator is deterministic: same inputs → same outputs.

#### Scenario: Test suite generated for Starter tier

- GIVEN the output directory contains 10 Starter-scope components and global token files
- WHEN `test_suite_generator.py` generates `tests/tokens.test.ts`
- THEN the file imports the package's token exports and contains `describe('Token validity', ...)` with one test per global token file

#### Scenario: Component name with hyphen sanitized

- GIVEN a component named `date-picker` (kebab-case) needs to appear as a TypeScript identifier
- WHEN `test_suite_generator.py` processes the component list
- THEN `date-picker` is converted to `datePicker` (camelCase) for use as a variable name in test code
- AND the string `"date-picker"` is used as the display name in `describe(...)` blocks

---

### Requirement: Pre-flight guard prevents Governance Crew from running before Phase 4a

The `create_governance_crew` factory MUST check that `docs/component-index.json` exists and is a non-empty JSON object before instantiating tasks. If the check fails, it SHALL raise `RuntimeError` with a descriptive message.

#### Acceptance Criteria

- [ ] `create_governance_crew("output_dir")` raises `RuntimeError` when `docs/component-index.json` is absent.
- [ ] `create_governance_crew("output_dir")` raises `RuntimeError` when `docs/component-index.json` is empty (`{}`).
- [ ] When the check passes, the crew is instantiated without error.
- [ ] The error message includes the expected file path for operator debugging.

#### Scenario: Pre-flight blocks on missing file

- GIVEN `docs/component-index.json` does not exist in the output directory
- WHEN `create_governance_crew(output_dir)` is called
- THEN it raises `RuntimeError("Documentation Crew output not found at <path> — ensure Phase 4a completes before Phase 4b")`
- AND no `Crew` object is constructed
