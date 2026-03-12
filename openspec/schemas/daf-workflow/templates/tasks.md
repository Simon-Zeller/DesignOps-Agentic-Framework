# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.

## 0. Pre-flight

- [ ] 0.1 Create feature branch: `feat/{{change-name}}` (or `fix/`, `refactor/`)
- [ ] 0.2 Verify clean working tree (`git status`)
- [ ] 0.3 Install/update dependencies if needed

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code.
     Each test maps to a case from tdd.md. -->

- [ ] 1.1 [Create/update test file for feature area 1]
- [ ] 1.2 [Create/update test file for feature area 2]
- [ ] 1.3 Verify all new tests FAIL (red phase confirmation)

## 2. Implementation (TDD — Green Phase)

<!-- Write the minimum production code to make tests pass.
     Group by crew/phase alignment where applicable. -->

- [ ] 2.1 [Implementation task — make test 1.1 pass]
- [ ] 2.2 [Implementation task — make test 1.2 pass]
- [ ] 2.3 Verify all tests PASS (green phase confirmation)

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Clean up implementation — remove duplication, improve naming
- [ ] 3.2 Ensure all tests still pass after refactor
- [ ] 3.3 Review code against design.md decisions

## 4. Integration & Quality

- [ ] 4.1 Run full linter (`ruff check` / `eslint` / project linter)
- [ ] 4.2 Run type checker (`pyright` / `tsc --noEmit`)
- [ ] 4.3 Fix all lint and type errors — zero warnings policy
- [ ] 4.4 Run full test suite (not just new tests)
- [ ] 4.5 Verify no regressions in existing tests

## 5. Git Hygiene

- [ ] 5.1 Stage changes with meaningful, atomic commits (conventional commits)
- [ ] 5.2 Ensure no untracked files left behind
- [ ] 5.3 Rebase on latest main if needed
- [ ] 5.4 Push feature branch

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main (`git checkout main && git merge feat/{{change-name}}`)
- [ ] 6.3 Push main (`git push origin main`)
- [ ] 6.4 Delete local feature branch (`git branch -d feat/{{change-name}}`)
- [ ] 6.5 Delete remote feature branch (`git push origin --delete feat/{{change-name}}`)
- [ ] 6.6 Verify clean state (`git branch -a` — feature branch gone)
