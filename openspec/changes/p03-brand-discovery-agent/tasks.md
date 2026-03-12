# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.

## 0. Pre-flight

- [ ] 0.1 Create feature branch: `feat/p03-brand-discovery-agent`
- [ ] 0.2 Verify clean working tree (`git status`)
- [ ] 0.3 Confirm `jsonschema` and `pydantic` are in `pyproject.toml` dependencies; add if missing

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code. Each test maps to a case from tdd.md. -->

- [ ] 1.1 Create `tests/test_brand_discovery_agent.py` with all test functions as stubs (use `pytest.fail("not implemented")` for each)
- [ ] 1.2 Add `BrandProfileSchemaValidator` unit tests: minimal valid profile, missing `name`, invalid archetype values (parametrized), invalid hex (parametrized), natural language color, out-of-bounds `scaleRatio` (parametrized)
- [ ] 1.3 Add `ArchetypeResolver` unit tests: all 5 archetypes return complete dicts (parametrized), enterprise-b2b defaults match PRD, mobile-first defaults (AAA, starter, compact), multi-brand defaults (brandOverrides, full themes)
- [ ] 1.4 Add `ConsistencyChecker` unit tests: consistent profile returns `[]`, compact+large baseUnit is error, mobile-first+comprehensive is warning, multi-brand+brandOverrides=False is warning, expressive motion+AAA is warning
- [ ] 1.5 Add `DefaultFiller` unit tests: user values are not overridden, minimal profile gains all fields, `_filled_fields` tracks what was defaulted
- [ ] 1.6 Add `BrandProfile` Pydantic model tests: valid profile constructs, extra fields are stripped
- [ ] 1.7 Add `daf generate` CLI tests: missing profile file exits code 1, `--profile` loads from path (mocked agent), `--yes` skips gate (mocked agent), gate `y` writes file (mocked agent), gate `N` does not write file, Enter treated as rejection
- [ ] 1.8 Add Human Gate summary display tests: `(default)` vs `(specified)` labels, warnings section shown when `_warnings` present
- [ ] 1.9 Verify all new tests **FAIL** (red phase — stubs should all fail or error on import)

## 2. Implementation (TDD — Green Phase)

### Phase 1: Package structure and Pydantic model

- [ ] 2.1 Create `src/daf/agents/__init__.py` (empty package marker)
- [ ] 2.2 Create `src/daf/tools/__init__.py` (empty package marker)
- [ ] 2.3 Create `src/daf/models.py` with `BrandProfile` Pydantic model mirroring the §6 schema; configure `model_config = ConfigDict(extra="ignore")` to strip extra fields
- [ ] 2.4 Verify Pydantic model tests pass (tasks 1.6)

### Phase 2: Deterministic tools

- [ ] 2.5 Create `src/daf/tools/brand_profile_validator.py` — `BrandProfileSchemaValidator(BaseTool)` that validates a profile dict against a JSON Schema definition of §6; returns `{"valid": bool, "errors": [{"field": str, "message": str}]}`
- [ ] 2.6 Verify `BrandProfileSchemaValidator` tests pass (tasks 1.2)
- [ ] 2.7 Create `src/daf/tools/archetype_resolver.py` — `ArchetypeResolver(BaseTool)` with a complete defaults dict for all 5 archetypes; returns the defaults dict for the given archetype string
- [ ] 2.8 Verify `ArchetypeResolver` tests pass (tasks 1.3)
- [ ] 2.9 Create `src/daf/tools/consistency_checker.py` — `ConsistencyChecker(BaseTool)` with a flat list of `(predicate, field, message, severity)` tuples; iterates all rules against the profile; returns list of triggered findings
- [ ] 2.10 Verify `ConsistencyChecker` tests pass (tasks 1.4)
- [ ] 2.11 Create `src/daf/tools/default_filler.py` — `DefaultFiller(BaseTool)` that merges archetype defaults into the profile, records filled fields in `_filled_fields`, returns the merged profile
- [ ] 2.12 Verify `DefaultFiller` tests pass (tasks 1.5)

### Phase 3: CrewAI Agent and Task

- [ ] 2.13 Create `src/daf/agents/brand_discovery.py` — `BrandDiscoveryAgent`: CrewAI `Agent` with role, goal, backstory; tools list `[BrandProfileSchemaValidator(), ArchetypeResolver(), ConsistencyChecker(), DefaultFiller()]`; `llm` set to Tier 2 Claude Sonnet via `DAF_TIER2_MODEL` env var (default `claude-sonnet-4-20250514`)
- [ ] 2.14 Define `create_brand_discovery_task(raw_profile: dict) -> Task` — Task T1 with `output_pydantic=BrandProfile`; description instructs the agent to: run validator, fail on errors; run resolver with archetype; run consistency checker, fail on error-severity; run default filler; annotate natural language color descriptions; return enriched profile
- [ ] 2.15 Define `run_brand_discovery(raw_profile: dict) -> BrandProfile` — creates the Crew with the single agent and task T1, kicks off, returns the `BrandProfile` Pydantic output; raises `ValueError` with structured errors on task failure

### Phase 4: `daf generate` CLI command and Human Gate

- [ ] 2.16 Add `generate` command to `src/daf/cli.py`: accept `--profile PATH` (optional) and `--yes` (flag); load profile from path or `Path.cwd() / "brand-profile.json"`; exit with code 1 and error message if file not found
- [ ] 2.17 In `generate` command: call `run_brand_discovery(raw_profile)`, catch `ValueError` to print structured errors and exit code 1
- [ ] 2.18 Implement `render_gate_summary(profile: BrandProfile) -> str` — formats the enriched profile as a human-readable summary with `(default)` / `(specified)` labels and a "Warnings" section if `_warnings` is non-empty
- [ ] 2.19 Implement the Human Gate prompt: if not `--yes`, print the summary, prompt `"Approve this brand profile and start generation? [y/N]"`, require explicit `y`; on approval write final `brand-profile.json` and print confirmation; on rejection exit code 1 with guidance
- [ ] 2.20 Verify all CLI and Human Gate tests pass (tasks 1.7, 1.8)

## 3. Refactor (TDD — Refactor Phase)

- [ ] 3.1 Review `ConsistencyChecker` rule list: ensure each rule has a clear, actionable message; extract constants for severity levels
- [ ] 3.2 Review `ArchetypeResolver` defaults: cross-check all 5 archetypes against PRD §4.1 descriptions; correct any mismatches
- [ ] 3.3 Review `render_gate_summary`: ensure the output is scannable and not overwhelming for a real 25-field profile
- [ ] 3.4 Review `BrandProfile` Pydantic model: confirm all §6 optional fields have sensible `default=None` values so partial profiles construct without error
- [ ] 3.5 Ensure all tests still pass after refactor (`pytest tests/test_brand_discovery_agent.py`)

## 4. Integration & Quality

- [ ] 4.1 Run full linter: `ruff check src/ tests/`
- [ ] 4.2 Run type checker: `pyright src/`
- [ ] 4.3 Fix all lint and type errors — zero warnings policy
- [ ] 4.4 Run full test suite: `pytest tests/ -v --ignore=tests/test_brand_discovery_agent.py -m "not integration"` (confirm no regressions)
- [ ] 4.5 Run new tests: `pytest tests/test_brand_discovery_agent.py -v -m "not integration"` — all must pass
- [ ] 4.6 Run coverage: `pytest tests/test_brand_discovery_agent.py --cov=src/daf/tools --cov=src/daf/agents --cov=src/daf/models --cov-report=term-missing -m "not integration"` — verify ≥80% line coverage, ≥70% branch coverage
- [ ] 4.7 (Optional, requires `ANTHROPIC_API_KEY`) Run integration tests: `pytest tests/test_brand_discovery_agent.py -m integration -v`

## 5. Git Hygiene

- [ ] 5.1 Stage with atomic conventional commits:
  - `feat(tools): add BrandProfileSchemaValidator, ArchetypeResolver, ConsistencyChecker, DefaultFiller`
  - `feat(models): add BrandProfile Pydantic model (§6 schema)`
  - `feat(agents): add BrandDiscoveryAgent and Task T1 (CrewAI)`
  - `feat(cli): add daf generate command with Human Gate prompt`
  - `test: add test_brand_discovery_agent.py (Agent 1, all tools, CLI)`
- [ ] 5.2 Verify no untracked files or unstaged changes (`git status`)
- [ ] 5.3 Rebase on latest main if needed: `git rebase main`
- [ ] 5.4 Push feature branch: `git push origin feat/p03-brand-discovery-agent`

## 6. Delivery

- [ ] 6.1 All tasks above are checked
- [ ] 6.2 Merge feature branch into main: `git checkout main && git merge feat/p03-brand-discovery-agent`
- [ ] 6.3 Push main: `git push origin main`
- [ ] 6.4 Delete local feature branch: `git branch -d feat/p03-brand-discovery-agent`
- [ ] 6.5 Delete remote feature branch: `git push origin --delete feat/p03-brand-discovery-agent`
- [ ] 6.6 Verify clean state: `git branch -a` — feature branch gone
