# Verification: {{change-name}}

> Definition of Done checklist. Complete this AFTER implementation (/opsx:apply).
> Every item must be checked before the change can be archived.

---

## 1. Tests

- [ ] 1.1 All new tests pass
- [ ] 1.2 All existing tests pass (no regressions)
- [ ] 1.3 Test coverage meets targets defined in tdd.md
- [ ] 1.4 Edge case / error scenario tests included and passing
- [ ] 1.5 Tests are meaningful (not trivial assertions)

## 2. Code Quality

- [ ] 2.1 Zero lint errors (`ruff` / `eslint` / project linter)
- [ ] 2.2 Zero type errors (`pyright` / `tsc --noEmit`)
- [ ] 2.3 No hardcoded values where tokens/config should be used
- [ ] 2.4 No commented-out code or debug statements left behind
- [ ] 2.5 Code follows project conventions and patterns from design.md

## 3. Manual Testing

<!-- Human verification of the implemented features -->

- [ ] 3.1 Feature works as described in the proposal
- [ ] 3.2 Happy path scenarios from specs verified manually
- [ ] 3.3 Edge case scenarios verified manually
- [ ] 3.4 Error handling behaves as specified
- [ ] 3.5 No visual regressions (if applicable)
- [ ] 3.6 Performance acceptable (no obvious slowdowns)

### Manual Test Evidence

<!-- Record what was tested and the result -->

| Scenario | Steps Taken | Expected | Actual | Pass? |
|----------|-------------|----------|--------|-------|
|          |             |          |        |       |

## 4. Acceptance Criteria

<!-- Copy acceptance criteria from specs and verify each one -->

- [ ] 4.1 [Criterion from specs]
- [ ] 4.2 [Criterion from specs]
<!-- ... all criteria from specs must be listed and checked -->

## 5. Git & Delivery

- [ ] 5.1 Feature branch is up to date with main
- [ ] 5.2 Commits are atomic and use conventional commit format
- [ ] 5.3 No merge conflicts
- [ ] 5.4 PR created with description linking to this change
- [ ] 5.5 CI pipeline passes (if applicable)

## 6. Documentation

- [ ] 6.1 Code changes are self-documenting or have necessary comments
- [ ] 6.2 Public APIs / interfaces are documented
- [ ] 6.3 README or docs updated if behavior changed
- [ ] 6.4 Architecture decision records created if needed

## 7. Final Sign-off

- [ ] 7.1 All sections above are complete
- [ ] 7.2 Change is ready for code review / merge
- [ ] 7.3 Ready to archive (`/opsx:archive`)

---

**DoD Summary:**

| Gate | Status |
|------|--------|
| Tests pass | ⬜ |
| Zero lint/type errors | ⬜ |
| Manual QA complete | ⬜ |
| Acceptance criteria met | ⬜ |
| Git hygiene OK | ⬜ |
| Docs updated | ⬜ |
