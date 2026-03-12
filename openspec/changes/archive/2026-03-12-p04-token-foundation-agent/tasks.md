# Tasks

> Follow strict TDD order: write tests first, then implement, then verify.
> Check off each task as you complete it.

## 0. Pre-flight

- [x] 0.1 Create feature branch: `feat/p04-token-foundation-agent`
- [x] 0.2 Verify clean working tree (`git status`)
- [x] 0.3 Confirm `crewai`, `pydantic`, and `anthropic` are in `pyproject.toml` dependencies; add if missing

## 1. Test Scaffolding (TDD — Red Phase)

<!-- Write failing tests FIRST, before any production code. Each test maps to a case from tdd.md. -->

- [x] 1.1 Create `tests/test_color_palette_generator.py` with all test functions as stubs (`pytest.fail("not implemented")`): hex anchor test, tonal ordering test, `_color_notes` resolution test, lookup table fallback test (parametrized), absent roles produce no tokens test, multiple roles test
- [x] 1.2 Create `tests/test_modular_scale_calculator.py` with stubs: typography step-0 value test, spacing step-4 equals `4 × baseUnit` test, compact density 0.75× test (parametrized steps), archetype defaults fallback test (parametrized archetypes), all scale categories present test, flat scale edge case test, spacious density 1.33× test
- [x] 1.3 Create `tests/test_contrast_safe_pairer.py` with stubs: AA tier contrast ≥ 4.5:1 test, AAA tier darker step test, WCAG luminance formula accuracy test (parametrized reference pairs), no-passing-tone `passed=False` test, palette immutability test
- [x] 1.4 Create `tests/test_dtcg_formatter.py` with stubs: global tier no reference strings test, semantic tier only reference strings test, all tokens have `$value`+`$type`+`$description` test, self-check typo `ValueError` test, self-check missing step `ValueError` test, multi-theme `$extensions.themes` test, `tokens/` directory creation test, multi-brand override files test, output is valid UTF-8 JSON test
- [x] 1.5 Create `tests/test_token_foundation_agent.py` with stubs: task output lists 3 written files test, token counts in expected range test, AAA profile contrast pairs all pass test, multi-brand profile writes 5 files test, integration test stub (`@pytest.mark.integration`)
- [x] 1.6 Verify all new tests **FAIL** (red phase — stubs should fail on import or `pytest.fail`)

## 2. Implementation (TDD — Green Phase)

### Phase 1: Pydantic models

- [x] 2.1 Add `ContrastPairResult` Pydantic model to `src/daf/models.py`: fields `token_pair: str`, `contrast_ratio: float`, `passed: bool`, `alias_selected: str`
- [x] 2.2 Add `TokenFoundationOutput` Pydantic model to `src/daf/models.py`: fields `written_files: list[str]`, `token_counts: dict[str, int]`, `contrast_pairs: list[ContrastPairResult]`, `token_notes: str | None`
- [x] 2.3 Verify Pydantic model tests pass (any model-level assertions in `test_token_foundation_agent.py`)

### Phase 2: ColorPaletteGenerator tool

- [x] 2.4 Create `src/daf/tools/color_palette_generator.py` — `ColorPaletteGenerator(BaseTool)`:
  - Accept `colors: dict[str, str | None]` and `color_notes: dict[str, str]`
  - Implement hex extraction from `_color_notes` annotation strings (regex for `#[0-9A-Fa-f]{6}`)
  - Implement deterministic color name lookup table (≥20 common color names → hex)
  - Implement HSL tonal scale: step 500 = brand hex; steps 50–400 use linearly increasing L toward 95%; steps 600–950 use linearly decreasing L toward 5%; hue-shift ±5° for warmth/coolness
  - Return flat dict with keys `color.{role}.{step}` (only for non-None roles)
- [x] 2.5 Verify `ColorPaletteGenerator` tests pass (tasks 1.1)

### Phase 3: ModularScaleCalculator tool

- [x] 2.6 Create `src/daf/tools/modular_scale_calculator.py` — `ModularScaleCalculator(BaseTool)`:
  - Accept `typography: dict | None`, `spacing: dict | None`, `archetype: str`
  - Implement archetype defaults lookup for missing `typography`/`spacing` fields (reuse `ArchetypeResolver` data or duplicate inline)
  - Implement typography scale: 16 steps, `size_n = baseSize × scaleRatio^n` for `n` in `[-7, 8]`; output as `"{value}px"` strings with named steps (e.g., `xs`, `sm`, `base`, `lg`, `xl`, `2xl`, ...)
  - Implement spacing ladder: 12 steps as integer multiples of `baseUnit` (1×–12× with density modifier: `compact=0.75`, `default=1.0`, `spacious=1.33`)
  - Implement elevation scale: 6 steps as `box-shadow` CSS strings with increasing blur/spread
  - Implement border-radius scale: 6 named steps from `0` to `9999px`
  - Implement opacity: 10 steps as `{n}%` strings
  - Implement motion duration: 8 steps as `{n}ms` strings
  - Implement easing: 5 named `cubic-bezier(...)` / `linear` strings
  - Return nested dict grouped by category
- [x] 2.7 Verify `ModularScaleCalculator` tests pass (tasks 1.2)

### Phase 4: ContrastSafePairer tool

- [x] 2.8 Create `src/daf/tools/contrast_safe_pairer.py` — `ContrastSafePairer(BaseTool)`:
  - Implement WCAG 2.1 relative luminance helper (sRGB → linear → `0.2126R + 0.7152G + 0.0722B`)
  - Implement contrast ratio: `(L1 + 0.05) / (L2 + 0.05)` where `L1 > L2`
  - Define mandatory semantic pairings: `text.default`/`surface.default`, `text.inverse`/`interactive.primary.background`, `text.inverse`/`interactive.accent.background`
  - Iterate over all palette steps for each pairing; select the passing step with highest contrast; if none passes, record best attempt with `passed=False`
  - Accept `palette: dict[str, str]`, `accessibility: str` (`"AA"` or `"AAA"`) → `threshold = 4.5 if "AA" else 7.0`
  - Return `semantic_overrides: dict[str, str]` and `contrast_results: list[ContrastPairResult]`
- [x] 2.9 Verify `ContrastSafePairer` tests pass (tasks 1.3)

### Phase 5: WC3DTCGFormatter tool

- [x] 2.10 Create `src/daf/tools/dtcg_formatter.py` — `WC3DTCGFormatter(BaseTool)`:
  - Accept `global_palette: dict`, `scale_tokens: dict`, `semantic_overrides: dict`, `component_overrides: dict`, `themes: list[str]`, `brands: dict[str, dict]`, `output_dir: str`
  - Implement global tier serialization: flat token keys → nested DTCG structure with inferred `$type` from key name (`color.*` → `color`, `scale.font-size.*` → `dimension`, etc.)
  - Implement semantic tier serialization: each alias becomes `{group.token.step}` reference; add `$extensions.themes` for multi-theme profiles mapping each theme mode to its reference
  - Implement component tier serialization: component overrides referencing semantic tokens
  - Implement reference self-check: traverse all `$value` fields containing `{`; resolve each against the assembled global dict; raise `ValueError` with unresolvable reference path on failure
  - Implement file write: create `output_dir/tokens/` if absent; write 3 base files + `brands/<name>.tokens.json` per brand (brand override = set-difference from base semantic tier)
  - Return `list[str]` of written file paths
- [x] 2.11 Verify `WC3DTCGFormatter` tests pass (tasks 1.4)

### Phase 6: Token Foundation Agent and Task T2

- [x] 2.12 Create `src/daf/agents/token_foundation.py`:
  - Define `create_token_foundation_agent() -> Agent`: role "Token Foundation Specialist", goal (generate complete DTCG token set), backstory, tools `[ColorPaletteGenerator(), ModularScaleCalculator(), ContrastSafePairer(), WC3DTCGFormatter()]`, `llm` set to Tier 2 Claude Sonnet via `DAF_TIER2_MODEL` env var
  - Define `create_token_foundation_task(profile: BrandProfile, output_dir: str, context_tasks: list[Task] | None = None) -> Task`: Task T2 with `output_pydantic=TokenFoundationOutput`; description instructs agent to run all 4 tools in order; set `context=context_tasks` if provided
- [x] 2.13 Update `src/daf/agents/brand_discovery.py`: import `create_token_foundation_agent`, `create_token_foundation_task`; add task T2 wiring so Task T2 uses `context=[task_t1]`; update Crew definition to include both agents and both tasks in sequence
- [x] 2.14 Update `src/daf/agents/__init__.py` to export `create_token_foundation_agent`, `create_token_foundation_task`
- [x] 2.15 Update `src/daf/tools/__init__.py` to export `ColorPaletteGenerator`, `ModularScaleCalculator`, `ContrastSafePairer`, `WC3DTCGFormatter`
- [x] 2.16 Verify `TokenFoundationAgent` task output tests pass with mocked LLM (tasks 1.5, non-integration)

## 3. Refactor (TDD — Refactor Phase)

- [x] 3.1 Review `ColorPaletteGenerator`: ensure lookup table entries are tested; verify tonal scale handles pure-white and pure-black brand colors without producing invalid hex
- [x] 3.2 Review `ModularScaleCalculator`: confirm named typography steps align with conventional naming (xs/sm/base/lg/xl/2xl); check archetype defaults match PRD §4.1 descriptions
- [x] 3.3 Review `ContrastSafePairer`: verify the mandatory pairing list is complete (all pairings from PRD §3.2 theme contract); confirm `text.default`/`surface.default` uses the neutral scale correctly
- [x] 3.4 Review `WC3DTCGFormatter`: ensure `$type` inference covers all token categories (color, dimension, duration, cubic-bezier, number, shadow); add `$type` constants or an inference map instead of string literals
- [x] 3.5 Review task T2 description: confirm it references the output directory path so the formatter writes to the correct location in `daf generate` invocations
- [x] 3.6 Ensure all tests still pass after refactor (`pytest tests/ -m "not integration" -v`)

## 4. Integration & Quality

- [x] 4.1 Run full linter: `ruff check src/ tests/`
- [x] 4.2 Run type checker: `pyright src/`
- [x] 4.3 Fix all lint and type errors — zero warnings policy
- [x] 4.4 Run full test suite: `pytest tests/ -v -m "not integration"` — confirm no regressions in existing tests
- [x] 4.5 Run new tests only: `pytest tests/test_color_palette_generator.py tests/test_modular_scale_calculator.py tests/test_contrast_safe_pairer.py tests/test_dtcg_formatter.py tests/test_token_foundation_agent.py -v -m "not integration"` — all must pass
- [x] 4.6 Run coverage check: `pytest tests/test_color_palette_generator.py tests/test_modular_scale_calculator.py tests/test_contrast_safe_pairer.py tests/test_dtcg_formatter.py tests/test_token_foundation_agent.py --cov=src/daf/tools --cov=src/daf/agents/token_foundation --cov=src/daf/models --cov-report=term-missing -m "not integration"` — verify ≥80% line coverage, ≥70% branch coverage
- [x] 4.7 (Optional, requires `ANTHROPIC_API_KEY`) Run integration test: `pytest tests/test_token_foundation_agent.py -m integration -v`

## 5. Git Hygiene

- [x] 5.1 Stage changes with atomic conventional commits:
  - `feat: add ContrastPairResult and TokenFoundationOutput Pydantic models`
  - `feat: add ColorPaletteGenerator tool`
  - `feat: add ModularScaleCalculator tool`
  - `feat: add ContrastSafePairer tool`
  - `feat: add WC3DTCGFormatter tool`
  - `feat: add TokenFoundationAgent (Agent 2) and Task T2`
  - `feat: wire Task T2 into DS Bootstrap Crew task chain`
  - `test: add unit tests for token foundation tools and agent`
- [x] 5.2 Ensure no untracked files left behind
- [x] 5.3 Rebase on latest `main` if needed
- [x] 5.4 Push feature branch

## 6. Delivery

- [x] 6.1 All tasks above are checked
- [x] 6.2 Merge feature branch into main (`git checkout main && git merge feat/p04-token-foundation-agent`)
- [x] 6.3 Push main (`git push origin main`)
- [x] 6.4 Delete local feature branch (`git branch -d feat/p04-token-foundation-agent`)
- [x] 6.5 Delete remote feature branch (`git push origin --delete feat/p04-token-foundation-agent`)
- [x] 6.6 Verify clean state (`git branch -a` — feature branch gone)
