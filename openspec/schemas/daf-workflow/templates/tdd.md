# TDD Plan: {{change-name}}

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

<!-- What testing approach is used? Unit, integration, e2e? -->
<!-- What tools/frameworks? (Vitest, pytest, @testing-library, etc.) -->

## Test Cases

<!-- Derived from specs scenarios and design decisions.
     Each test case maps to a specific requirement/scenario from specs. -->

### [Feature Area 1]

#### Test: [Descriptive test name]

- **Maps to:** Requirement "[Name]" → Scenario "[Name]"
- **Type:** unit | integration | e2e
- **Given:** [Setup/precondition]
- **When:** [Action under test]
- **Then:** [Expected assertion]
- **File:** `path/to/test/file`

#### Test: [Next test]

- **Maps to:** Requirement "[Name]" → Scenario "[Name]"
- **Type:** unit | integration | e2e
- **Given:** [Setup/precondition]
- **When:** [Action under test]
- **Then:** [Expected assertion]
- **File:** `path/to/test/file`

### [Feature Area 2]

<!-- Repeat as needed -->

## Edge Case Tests

<!-- Tests for boundary conditions, error states, invalid inputs -->

#### Test: [Edge case name]

- **Maps to:** Requirement "[Name]" → Scenario "[Error case]"
- **Type:** unit | integration
- **Given:** [Invalid or boundary state]
- **When:** [Action]
- **Then:** [Error handling / graceful behavior]

## Test Coverage Targets

<!-- Minimum coverage thresholds for this change -->

| Metric | Target | Rationale |
|--------|--------|-----------|
| Line coverage | ≥80% | PRD quality gate requirement |
| Branch coverage | ≥70% | Covers conditional logic paths |
| A11y rules passing | 100% critical | Zero critical a11y violations |

## Test File Inventory

<!-- All test files this change will create or modify -->

| File | Status | Description |
|------|--------|-------------|
|      | new/modified |           |
