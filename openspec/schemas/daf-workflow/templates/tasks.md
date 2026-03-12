# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.
>
> **Git checkpoint rule:** After each numbered section, run `git add -A && git status`
> to verify nothing is untracked. Commit with a conventional commit message before
> moving to the next section. This prevents files from silently going missing.

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
- [ ] 1.4 **Git checkpoint:** `git add -A && git commit -m "test: scaffold failing tests for {{change-name}}"`

## 2. Implementation (TDD — Green Phase)

<!-- Write the minimum production code to make tests pass.
     Group by crew/phase alignment where applicable. -->

- [ ] 2.1 [Implementation task — make test 1.1 pass]
- [ ] 2.2 [Implementation task — make test 1.2 pass]
- [ ] 2.3 Verify all tests PASS (green phase confirmation)
- [ ] 2.4 **Git checkpoint:** `git add -A && git commit -m "feat: implement {{change-name}}"`

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Clean up implementation — remove duplication, improve naming
- [ ] 3.2 Ensure all tests still pass after refactor
- [ ] 3.3 Review code against design.md decisions
- [ ] 3.4 **Git checkpoint:** `git add -A && git commit -m "refactor: clean up {{change-name}}"`

## 4. Integration & Quality

- [ ] 4.1 Run full linter (`ruff check` / `eslint` / project linter)
- [ ] 4.2 Run type checker (`pyright` / `tsc --noEmit`)
- [ ] 4.3 Fix all lint and type errors — zero warnings policy
- [ ] 4.4 Run full test suite (not just new tests)
- [ ] 4.5 Verify no regressions in existing tests
- [ ] 4.6 **Git checkpoint:** `git add -A && git commit -m "chore: fix lint and type errors for {{change-name}}"` (skip if no changes)

## 5. Final Verification & Push

- [ ] 5.1 `git status` — confirm zero untracked files, zero unstaged changes
- [ ] 5.2 `git log --oneline main..HEAD` — review all commits on this branch
- [ ] 5.3 Rebase on latest main if needed (`git fetch origin && git rebase origin/main`)
- [ ] 5.4 Push feature branch (`git push origin feat/{{change-name}}`)

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main (`git checkout main && git merge feat/{{change-name}}`)
- [ ] 6.3 Push main (`git push origin main`)
- [ ] 6.4 Delete local feature branch (`git branch -d feat/{{change-name}}`)
- [ ] 6.5 Delete remote feature branch (`git push origin --delete feat/{{change-name}}`)
- [ ] 6.6 Verify clean state (`git branch -a` — feature branch gone, `git status` — clean)
