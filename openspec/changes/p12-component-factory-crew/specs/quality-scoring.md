# Specification: Quality Scoring and Gating

## Purpose

Defines the behavioral requirements for Agent 20 (Quality Scoring Agent) in the Component Factory Crew. Covers the five-sub-score composite quality formula, the 70/100 composite gate, report output format for `quality-scorecard.json`, per-component gate verdict tracking, retry escalation for below-threshold components, and the boundary with the Governance Crew's separate 80% test coverage gate.

---

## Requirements

### Requirement: Composite quality score computation

Agent 20 (Quality Scoring Agent) MUST compute a composite quality score (0–100) for every component processed by the Component Factory Crew. The score MUST be a weighted average of five sub-scores. Each sub-score is a percentage (0.0–1.0) multiplied by its weight.

Composite score formula:
```
composite = (test_coverage * 0.25)
          + (a11y_pass_rate * 0.25)
          + (token_compliance * 0.20)
          + (composition_depth_score * 0.15)
          + (spec_completeness * 0.15)
```

Sub-score definitions:
- **test_coverage (25%)**: Line coverage percentage from Vitest LCOV output for the component file. Range: 0.0–1.0. Source: `coverage_reporter.py`. If coverage data is unavailable, defaults to `0.0` with `coverage_unavailable: true` flag.
- **a11y_pass_rate (25%)**: Percentage of axe-core rules passing for the component (from `a11y-audit.json`). Range: 0.0–1.0. Source: Agent 19's audit output.
- **token_compliance (20%)**: Percentage of style value assignments in the component that reference compiled token variables (not hardcoded values). Range: 0.0–1.0. Source: `composition_rule_engine.py` token compliance scan.
- **composition_depth_score (15%)**: Score based on composition approach: primitives-only composition (depth ≤ 5) = 1.0; mixed primitive/DOM composition = 0.5; direct DOM elements present = 0.0. Source: `composition-audit.json`.
- **spec_completeness (15%)**: Percentage of required spec fields that are present and non-empty. Range: 0.0–1.0. Source: Agent 17's validation output.

All sub-scores and the composite MUST be recorded per component in `quality-scorecard.json`.

#### Acceptance Criteria

- [ ] A composite score (0–100) is computed for every component.
- [ ] The score is the weighted sum of exactly five sub-scores as defined above.
- [ ] Each sub-score is individually recorded in `quality-scorecard.json`.
- [ ] Components with `coverage_unavailable: true` show `test_coverage: 0.0` and the flag in their score record.
- [ ] `score_calculator.py` produces deterministic results given the same sub-score inputs.

#### Scenario: Button with full coverage and clean a11y

- GIVEN `Button.tsx` has 95% line coverage, 100% axe-core pass rate, 100% token compliance, primitives-only composition (score 1.0), and all required spec fields present (1.0)
- WHEN Agent 20 computes the composite via `score_calculator.py`
- THEN `composite = (0.95 * 0.25) + (1.0 * 0.25) + (1.0 * 0.20) + (1.0 * 0.15) + (1.0 * 0.15) = 0.9875 * 100 = 98.75`
- AND `quality-scorecard.json` records `Button` with `composite: 98.75, gate: "passed"`

#### Scenario: Component with missing coverage data

- GIVEN `Accordion.tsx` has no Vitest coverage data available (coverage was not instrumented)
- WHEN `coverage_reporter.py` returns `None`
- THEN `score_calculator.py` substitutes `test_coverage = 0.0` and sets `coverage_unavailable: true`
- AND the composite is computed using `0.0` for the test coverage sub-score
- AND `quality-scorecard.json` records `Accordion` with `coverage_unavailable: true` and a Warning entry

#### Scenario: Component with hardcoded style values

- GIVEN `Badge.tsx` has 3 of 10 style value assignments using hardcoded hex colors instead of token variables
- WHEN `composition_rule_engine.py` reports `token_compliance: 0.7`
- THEN the token compliance sub-score is `0.7`
- AND this contributes `0.7 * 0.20 = 0.14` to the composite rather than the maximum `0.20`

---

### Requirement: 70/100 composite quality gate

Agent 20 MUST apply a 70/100 composite gate to every component score. Components with a composite score ≥ 70 receive a `gate: "passed"` verdict. Components with a composite score < 70 receive a `gate: "failed"` verdict and a structured rejection payload written for Agent 6 retry routing.

Gate behavior:
- Gate failure is NOT a crew-level fatal error; the crew continues scoring remaining components
- Gate failures trigger Agent 6 to re-invoke the Design-to-Code → Component Factory pipeline for failing components only (targeted retry, not full-crew retry)
- If a component fails the gate after 3 full retry cycles, its verdict is updated to `gate: "failed-final"` and flagged for operator review
- The 70/100 gate is independent from the Governance Crew's 80% test coverage gate (Quality Gate Agent 30); a component can pass 70/100 composite but still fail at the Governance phase if test coverage is below 80%

#### Acceptance Criteria

- [ ] Every component with a composite score ≥ 70 is recorded as `gate: "passed"` in `quality-scorecard.json`.
- [ ] Every component with a composite score < 70 is recorded as `gate: "failed"` and a structured rejection payload is written.
- [ ] Gate failure does not stop quality scoring for other components.
- [ ] `threshold_gate.py` returns a list of passing and failing components.
- [ ] After 3 retry cycles, components that still fail are recorded as `gate: "failed-final"`.

#### Scenario: Component scores 68/100 — gate failure

- GIVEN `DatePicker.tsx` has computed composite score `68.0`
- WHEN `threshold_gate.py` applies the 70/100 gate
- THEN `quality-scorecard.json` records `DatePicker` with `composite: 68.0, gate: "failed"`
- AND a structured rejection payload is written for Agent 6 specifying `component: "DatePicker", gate_score: 68.0, threshold: 70.0`
- AND scoring continues for remaining components

#### Scenario: Component scores exactly 70/100 — gate pass

- GIVEN `Tooltip.tsx` has computed composite score `70.0`
- WHEN `threshold_gate.py` applies the 70/100 gate
- THEN `quality-scorecard.json` records `Tooltip` with `composite: 70.0, gate: "passed"`
- AND no rejection payload is written

#### Scenario: Component fails gate after 3 retry cycles

- GIVEN `DataGrid.tsx` has failed the 70/100 gate on its initial run and 2 subsequent retry cycles
- WHEN Agent 20 scores the component after the third retry
- THEN `quality-scorecard.json` records `DataGrid` with `gate: "failed-final", retry_cycles: 3`
- AND a `needs_operator_review: true` flag is added to the scorecard entry
- AND no further rejection payload is written (retry escalation stops)

---

### Requirement: Quality scorecard report format

Agent 20 MUST write `reports/quality-scorecard.json` with a standardised structure after all components are scored. The report MUST include a summary section with aggregate statistics and a per-component breakdown.

Required report structure:
```json
{
  "generated_at": "<ISO timestamp>",
  "pipeline_run_id": "<run id from brand-profile.json>",
  "summary": {
    "total_components": <int>,
    "gate_passed": <int>,
    "gate_failed": <int>,
    "gate_failed_final": <int>,
    "average_composite": <float>,
    "coverage_unavailable_count": <int>
  },
  "components": {
    "<ComponentName>": {
      "composite": <float 0-100>,
      "gate": "passed" | "failed" | "failed-final",
      "retry_cycles": <int>,
      "sub_scores": {
        "test_coverage": <float 0-1> | null,
        "a11y_pass_rate": <float 0-1>,
        "token_compliance": <float 0-1>,
        "composition_depth_score": <float 0-1>,
        "spec_completeness": <float 0-1>
      },
      "flags": {
        "coverage_unavailable": <bool>,
        "needs_operator_review": <bool>
      },
      "warnings": [<string>]
    }
  }
}
```

#### Acceptance Criteria

- [ ] `reports/quality-scorecard.json` is written after all components are scored.
- [ ] The file conforms to the required structure (all keys present).
- [ ] The `summary` section accurately reflects the per-component data.
- [ ] Each component entry contains all five sub-scores.
- [ ] `generated_at` is a valid ISO 8601 timestamp.
- [ ] The file is valid JSON (parseable by `json.loads`).

#### Scenario: Scorecard written after full crew run

- GIVEN 10 components are scored: 8 pass, 1 fails gate, 1 has `coverage_unavailable`
- WHEN Agent 20 writes the scorecard via `report_writer.py`
- THEN `quality-scorecard.json` has `summary.total_components: 10`, `summary.gate_passed: 8`, `summary.gate_failed: 1`
- AND the component with missing coverage has `flags.coverage_unavailable: true` and `sub_scores.test_coverage: 0.0`

---

### Requirement: Boundary with Governance Crew quality gate

The Component Factory Crew's 70/100 composite gate and the Governance Crew's Quality Gate Agent (30) 80% minimum test coverage gate are INDEPENDENT checks. Passing the 70/100 composite does NOT guarantee passing the 80% coverage gate.

Agent 20 MUST record the test coverage sub-score in a way that is directly consumable by Quality Gate Agent (30), but MUST NOT make gate decisions on behalf of the Governance Crew.

#### Acceptance Criteria

- [ ] `quality-scorecard.json` contains the raw test coverage percentage (0.0–1.0) for every component, not just a pass/fail.
- [ ] No coverage threshold enforcement is applied in `quality-scorecard.json` beyond recording the value.
- [ ] The `coverage_reporter.py` tool's output is stored verbatim in the per-component record.
- [ ] Quality Gate Agent (30) in the Governance Crew reads `quality-scorecard.json` to apply the 80% threshold independently.

#### Scenario: Component passes 70/100 composite but coverage is 75%

- GIVEN `Navigation.tsx` has composite `72.0` (gate: passed) but test line coverage of 75% (below the Governance Crew's 80% threshold)
- WHEN Agent 20 writes the scorecard
- THEN `quality-scorecard.json` records `composite: 72.0, gate: "passed", sub_scores.test_coverage: 0.75`
- AND no coverage gate failure is recorded by Agent 20 (the 80% gate is Governance Crew's responsibility)
- AND Quality Gate Agent (30) will later read `0.75` and apply its own 0.80 threshold

---

### Requirement: A11y audit and composition audit report format

Agent 20 MUST consolidate audit data from Agents 17–19 and write `reports/a11y-audit.json` and `reports/composition-audit.json` alongside `quality-scorecard.json`. These reports provide detailed per-component audit trails for downstream crews and operators.

#### Acceptance Criteria

- [ ] `reports/a11y-audit.json` contains one entry per component with: `aria_patched`, `keyboard_patched`, `focus_trap_patched`, `aaaa_focus_visible_patched` (if AAA), `patch_failed`, `correction_attempts`, and `a11y_pass_rate`.
- [ ] `reports/composition-audit.json` contains one entry per component with: `composition_valid`, `violations` (list), `forbidden_nesting` (list), `depth`, and `composition_depth_score`.
- [ ] Both files are valid JSON and written before `quality-scorecard.json`.
- [ ] Both files are written even if no violations or patches were found (empty arrays for clean components).

#### Scenario: Clean run with no issues

- GIVEN all 10 components pass spec validation, composition checks, and a11y enforcement with zero patches
- WHEN Agent 20 writes the three reports
- THEN `a11y-audit.json` has all components with `aria_patched: false, keyboard_patched: false, patch_failed: false`
- AND `composition-audit.json` has all components with `composition_valid: true, violations: [], forbidden_nesting: []`
- AND `quality-scorecard.json` has all components with `gate: "passed"`
