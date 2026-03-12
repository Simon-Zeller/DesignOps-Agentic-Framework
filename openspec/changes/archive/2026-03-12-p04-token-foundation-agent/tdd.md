# TDD Plan: p04-token-foundation-agent

> This artifact is written BEFORE implementation. Tests are defined first,
> then implementation makes them pass. Do not skip this artifact.

## Test Strategy

This change introduces one CrewAI Agent, four deterministic tools, two Pydantic models, and task-chain wiring within the DS Bootstrap Crew. Tests are written in **pytest**.

Three test types are used:

1. **Unit tests** — each tool is tested in isolation without a live LLM; inputs are fixture dicts derived from realistic Brand Profiles; outputs are asserted at the structural and value level
2. **Integration tests** — test the full Agent 2 task with a live Anthropic API call; gated behind `@pytest.mark.integration` and excluded from the default `pytest` run
3. **Task chain tests** — test that T2 fires after T1 and that `TokenFoundationOutput` contains the expected file paths; uses a fixture-driven `BrandProfile` as T1 output and a `tmp_path` for file writes

Coverage target: ≥80% line coverage, ≥70% branch coverage per PRD quality gate.

Test files:
- `tests/test_color_palette_generator.py` — ColorPaletteGenerator
- `tests/test_modular_scale_calculator.py` — ModularScaleCalculator
- `tests/test_contrast_safe_pairer.py` — ContrastSafePairer
- `tests/test_dtcg_formatter.py` — WC3DTCGFormatter
- `tests/test_token_foundation_agent.py` — agent task output, T2 task wiring, `TokenFoundationOutput` model

---

## Test Cases

### ColorPaletteGenerator

#### Test: Hex color generates 11-step tonal scale anchored at step 500

- **Maps to:** Requirement "Color Palette Generation" → Scenario "Standard hex color generates full tonal scale"
- **Type:** unit
- **Given:** profile with `colors.primary = "#3D72B4"`, `_color_notes = {}`
- **When:** `ColorPaletteGenerator().run(colors={"primary": "#3D72B4"}, color_notes={})` is called
- **Then:** result contains exactly 11 keys: `color.primary.50` through `color.primary.950`
- AND `result["color.primary.500"] == "#3D72B4"` (exact brand anchor preserved)
- AND all values match `#[0-9A-Fa-f]{6}`
- **File:** `tests/test_color_palette_generator.py`

#### Test: Lighter steps have higher lightness than step 500

- **Maps to:** Requirement "Color Palette Generation" → Scenario "Standard hex color generates full tonal scale"
- **Type:** unit
- **Given:** any brand hex with mid-range lightness (e.g., `#3D72B4`)
- **When:** `ColorPaletteGenerator().run(...)` is called
- **Then:** HSL lightness of `color.primary.50` > HSL lightness of `color.primary.200` > ... > `color.primary.500`
- AND HSL lightness of `color.primary.950` < `color.primary.800` < ... < `color.primary.500`
- **File:** `tests/test_color_palette_generator.py`

#### Test: `_color_notes` hex annotation is used as anchor

- **Maps to:** Requirement "Color Palette Generation" → Scenario "Natural language color resolved via `_color_notes`"
- **Type:** unit
- **Given:** `colors.primary = "ocean blue"`, `_color_notes = {"colors.primary": "Interpreted as #1E6FA8 — deep professional blue"}`
- **When:** `ColorPaletteGenerator().run(...)` is called
- **Then:** `result["color.primary.500"] == "#1E6FA8"` (hex extracted from annotation)
- **File:** `tests/test_color_palette_generator.py`

#### Test: Lookup table resolves common color name when `_color_notes` provides no hex

- **Maps to:** Requirement "Color Palette Generation" → Scenario "Unresolvable color falls back to lookup table"
- **Type:** unit — parametrized over a selection of common color names (e.g., `"cerulean"`, `"coral"`, `"navy"`)
- **Given:** `colors.primary = <color_name>`, `_color_notes = {}`
- **When:** `ColorPaletteGenerator().run(...)` is called
- **Then:** `result["color.primary.500"]` is a valid `#RRGGBB` hex code
- AND the tool does not raise an exception
- **File:** `tests/test_color_palette_generator.py`

#### Test: Roles absent from profile produce no tokens

- **Maps to:** Requirement "Color Palette Generation" → Scenario "Profile with only primary color defined"
- **Type:** unit
- **Given:** `colors = {"primary": "#FF5733"}` — all other roles `None`
- **When:** `ColorPaletteGenerator().run(...)` is called
- **Then:** result contains only keys with prefix `color.primary.*`
- AND there are no keys with `color.secondary.*`, `color.accent.*`, etc.
- **File:** `tests/test_color_palette_generator.py`

#### Test: Multiple color roles each get independent 11-step scales

- **Maps to:** Requirement "Color Palette Generation" → Acceptance criteria (all defined roles)
- **Type:** unit
- **Given:** `colors = {"primary": "#3D72B4", "secondary": "#2ECC71", "accent": "#E74C3C", "neutral": "#95A5A6"}`
- **When:** `ColorPaletteGenerator().run(...)` is called
- **Then:** result contains 4 × 11 = 44 token keys
- AND each role's step 500 equals its input hex exactly
- **File:** `tests/test_color_palette_generator.py`

---

### ModularScaleCalculator

#### Test: Typography scale step 0 equals baseSize

- **Maps to:** Requirement "Modular Scale Computation" → Scenario "Enterprise archetype with custom scale ratio"
- **Type:** unit
- **Given:** `typography = {"baseSize": 16, "scaleRatio": 1.25}`, `spacing = {"baseUnit": 4, "density": "default"}`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** `result["scale.font-size.base"]` (or equivalent step-0 key) equals `"16px"`
- AND `result["scale.font-size.lg"]` ≈ `"20px"` (within ±1px rounding)
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: Spacing scale step 4 equals 4 × baseUnit (default density)

- **Maps to:** Requirement "Modular Scale Computation" → Scenario "Enterprise archetype with custom scale ratio"
- **Type:** unit
- **Given:** `spacing = {"baseUnit": 4, "density": "default"}`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** `result["scale.spacing.4"]` equals `"16px"` (4 × 4)
- AND `result["scale.spacing.8"]` equals `"32px"` (4 × 8)
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: Compact density reduces spacing by ~0.75× (parametrized)

- **Maps to:** Requirement "Modular Scale Computation" → Scenario "Compact density halves effective spacing"
- **Type:** unit — parametrized over steps 2, 4, 8, 12
- **Given:** `spacing = {"baseUnit": 8, "density": "compact"}`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** each spacing step value is ≈ 0.75× the default-density value for the same step (±5% tolerance)
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: Missing typography config falls back to archetype defaults

- **Maps to:** Requirement "Modular Scale Computation" → Scenario "Missing typography config uses archetype defaults"
- **Type:** unit — parametrized over all 5 archetypes
- **Given:** `typography = None`, `archetype = <archetype_value>`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** result contains `scale.font-size.*` keys (no KeyError or ValueError)
- AND result contains `scale.spacing.*` keys
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: All required scale categories are produced

- **Maps to:** Requirement "Modular Scale Computation" → Acceptance criteria
- **Type:** unit
- **Given:** a standard `BrandProfile` fixture
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** result contains keys from all 7 categories: `scale.font-size.*`, `scale.spacing.*`, `scale.elevation.*`, `scale.radius.*`, `scale.opacity.*`, `scale.duration.*`, `scale.easing.*`
- AND the total token count matches the expected step counts (16 + 12 + 6 + 6 + 10 + 8 + 5 = 63 scale tokens)
- **File:** `tests/test_modular_scale_calculator.py`

---

### ContrastSafePairer

#### Test: AA tier selects a primary tone with ≥ 4.5:1 contrast against white

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Scenario "AA profile selects passing tone for text-on-primary"
- **Type:** unit
- **Given:** a palette generated from `primary: "#3D72B4"`, `accessibility = "AA"`
- **When:** `ContrastSafePairer().run(palette, accessibility="AA")` is called
- **Then:** the `semantic_overrides["interactive.primary.background"]` key maps to a global alias (e.g., `"color.primary.700"`)
- AND computing the WCAG contrast of that tone against white yields ≥ 4.5
- **File:** `tests/test_contrast_safe_pairer.py`

#### Test: AAA tier selects a higher-contrast tone than AA tier

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Scenario "AAA profile selects higher-contrast tone"
- **Type:** unit
- **Given:** same palette as above, compared between `accessibility = "AA"` and `accessibility = "AAA"`
- **When:** both `ContrastSafePairer().run(palette, accessibility="AA")` and `...("AAA")` are called
- **Then:** the AAA-selected step index is higher (darker) than the AA-selected step
- AND the AAA contrast ratio is ≥ 7:1
- **File:** `tests/test_contrast_safe_pairer.py`

#### Test: WCAG luminance formula matches reference values (parametrized)

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Acceptance criteria (no external dependencies)
- **Type:** unit — parametrized with known reference pairs: `(#FFFFFF vs #000000, 21:1)`, `(#3D72B4 vs #FFFFFF, ~4.01:1)`, `(#0A2D5A vs #FFFFFF, ~10.5:1)`
- **Given:** foreground/background hex pairs with known contrast ratios
- **When:** the WCAG luminance helper inside `ContrastSafePairer` is called
- **Then:** computed contrast ratio matches the expected value within ±0.1
- **File:** `tests/test_contrast_safe_pairer.py`

#### Test: No passing tone sets `ContrastPairResult.passed = False`

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Scenario "No passing tone available (edge case)"
- **Type:** unit
- **Given:** a synthesized palette where all primary steps fail 4.5:1 against white (simulated very light palette)
- **When:** `ContrastSafePairer().run(palette, accessibility="AA")` is called
- **Then:** does NOT raise an exception
- AND the relevant `ContrastPairResult.passed == False`
- AND `ContrastPairResult.contrast_ratio` equals the highest-achieved ratio
- **File:** `tests/test_contrast_safe_pairer.py`

#### Test: Tool does not modify global-tier palette dict

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Acceptance criteria (does not modify global tier)
- **Type:** unit
- **Given:** a palette dict passed to `ContrastSafePairer`
- **When:** `ContrastSafePairer().run(...)` is called
- **Then:** the input palette dict is unchanged after the call (deep equality before/after)
- **File:** `tests/test_contrast_safe_pairer.py`

---

### WC3DTCGFormatter

#### Test: Global tier file contains no DTCG reference strings

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Scenario "Global tier uses raw values only"
- **Type:** unit
- **Given:** a palette dict and scales dict populated with hex codes and px values
- **When:** `WC3DTCGFormatter().run(...)` is called with a `tmp_path` output directory
- **Then:** `base.tokens.json` is written
- AND no `$value` field in the file contains a `{` character (not a reference)
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Semantic tier file contains only DTCG reference strings as values

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Scenario "Semantic tier uses reference values only"
- **Type:** unit
- **Given:** a semantic overrides dict with alias strings like `"color.primary.700"`
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** `semantic.tokens.json` is written
- AND every `$value` field that is color-typed matches the pattern `\{[a-z0-9._-]+\}` (DTCG reference)
- AND no `$value` is a plain hex string in the semantic file
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Every token object has `$value`, `$type`, and `$description`

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Acceptance criteria
- **Type:** unit
- **Given:** standard fixture token dicts
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** for all three output files, every leaf node (a dict with `$value`) also contains `$type` and `$description`
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Self-check raises ValueError on broken reference (typo in alias key)

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Scenario "Self-check catches broken reference before write"
- **Type:** unit
- **Given:** a semantic overrides dict with a misspelled alias `"color.priary.700"` (typo)
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** `ValueError` is raised BEFORE any file is written
- AND the error message contains the broken reference string `{color.priary.700}`
- AND no file exists at the output path
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Multi-theme tokens include `$extensions.themes` block

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Scenario "Multi-theme semantic tokens include `$extensions.themes`"
- **Type:** unit
- **Given:** themes = `["light", "dark"]` with per-theme semantic overrides
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** affected semantic tokens in `semantic.tokens.json` contain `$extensions.themes` with both `"light"` and `"dark"` keys
- **File:** `tests/test_dtcg_formatter.py`

#### Test: `tokens/` directory is created if absent

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Acceptance criteria
- **Type:** unit
- **Given:** an output path inside a `tmp_path` that does not yet have a `tokens/` subdirectory
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** the `tokens/` directory is created
- AND all three JSON files are written inside it
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Multi-brand generates per-brand override files

- **Maps to:** Requirement "Multi-Brand Override File Generation" → Scenario "Two-brand profile generates two override files"
- **Type:** unit
- **Given:** brand profile with `archetype: "multi-brand"`, `themes.brands: ["brand-a", "brand-b"]` and per-brand overrides
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** `tokens/brands/brand-a.tokens.json` and `tokens/brands/brand-b.tokens.json` are both written
- AND neither file contains keys that match the base semantic tier 1:1 (only delta tokens present)
- **File:** `tests/test_dtcg_formatter.py`

---

### Token Foundation Agent (Task T2)

#### Test: Task T2 output lists three written file paths

- **Maps to:** Requirement "Task T2 Integration in DS Bootstrap Crew" → Scenario "T2 runs after T1 completes successfully"
- **Type:** unit (mocked LLM, real tools with `tmp_path`)
- **Given:** a fixture `BrandProfile` with `colors.primary = "#3D72B4"`, `archetype = "enterprise-b2b"`, all required fields filled
- **When:** `create_token_foundation_task(profile, output_dir=tmp_path)` is run via a single-agent CrewAI Crew with the LLM mocked
- **Then:** `TokenFoundationOutput.written_files` contains exactly 3 paths
- AND all 3 paths exist as files
- AND each file is valid JSON
- **File:** `tests/test_token_foundation_agent.py`

#### Test: Task T2 output `token_counts` sums to expected range

- **Maps to:** Requirement "Task T2 Integration in DS Bootstrap Crew" → Acceptance criteria
- **Type:** unit (mocked LLM, real tools)
- **Given:** same fixture `BrandProfile` as above
- **When:** task completes
- **Then:** `TokenFoundationOutput.token_counts["base"]` is in range `[100, 600]`
- AND `TokenFoundationOutput.token_counts["semantic"]` is in range `[40, 200]`
- AND `TokenFoundationOutput.token_counts["component"]` is in range `[10, 100]`
- **File:** `tests/test_token_foundation_agent.py`

#### Test: AAA accessibility profile results in all contrast pairs passing

- **Maps to:** Requirement "WCAG Contrast-Safe Semantic Alias Selection" → Acceptance criteria (AAA tier all pairings ≥ 7:1)
- **Type:** unit (mocked LLM, real tools)
- **Given:** a fixture `BrandProfile` with `accessibility = "AAA"` and a dark-enough primary color (`#0A2D5A`)
- **When:** task completes
- **Then:** `TokenFoundationOutput.contrast_pairs` all have `passed == True`
- AND each `contrast_ratio` is ≥ 7.0
- **File:** `tests/test_token_foundation_agent.py`

#### Test: Multi-brand profile writes brand override files in addition to base 3

- **Maps to:** Requirement "Multi-Brand Override File Generation" → Scenario "Two-brand profile generates two override files"
- **Type:** unit (mocked LLM, real tools)
- **Given:** a multi-brand `BrandProfile` fixture with `themes.brands = ["brand-a", "brand-b"]`
- **When:** task completes
- **Then:** `TokenFoundationOutput.written_files` contains 5 paths (3 base + 2 brand overrides)
- AND paths include `tokens/brands/brand-a.tokens.json` and `tokens/brands/brand-b.tokens.json`
- **File:** `tests/test_token_foundation_agent.py`

#### Test: Integration — real LLM call produces DTCG-valid output (gated)

- **Maps to:** Requirement "Task T2 Integration in DS Bootstrap Crew" → Scenario "T2 runs after T1 completes successfully"
- **Type:** integration (`@pytest.mark.integration`)
- **Given:** a fixture `BrandProfile` with a natural language color description for primary
- **When:** the full agent task is run with a live Claude Sonnet call
- **Then:** all three token files are written and valid JSON
- AND `base.tokens.json` contains no `{...}` reference strings
- AND `semantic.tokens.json` contains no raw hex strings
- **File:** `tests/test_token_foundation_agent.py`

---

## Edge Case Tests

#### Test: Empty colors dict produces no color tokens

- **Maps to:** Requirement "Color Palette Generation" → Acceptance criteria (no phantom tokens)
- **Type:** unit
- **Given:** `colors = {}` — no color roles defined
- **When:** `ColorPaletteGenerator().run(colors={}, color_notes={})` is called
- **Then:** returns an empty dict (no crash)
- **File:** `tests/test_color_palette_generator.py`

#### Test: Very small scaleRatio (1.0) produces flat typography scale

- **Maps to:** Requirement "Modular Scale Computation" → edge case
- **Type:** unit
- **Given:** `typography.scaleRatio = 1.0`, `typography.baseSize = 16`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** all `scale.font-size.*` steps equal `"16px"` (flat scale — `16 × 1.0^n`)
- AND no exception is raised
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: Spacious density increases spacing beyond default

- **Maps to:** Requirement "Modular Scale Computation" → Acceptance criteria (density modifier: spacious = 1.33×)
- **Type:** unit
- **Given:** `spacing = {"baseUnit": 8, "density": "spacious"}`
- **When:** `ModularScaleCalculator().run(...)` is called
- **Then:** each spacing step is ≈ 1.33× the default-density value (±5% tolerance)
- **File:** `tests/test_modular_scale_calculator.py`

#### Test: Self-check catches reference to non-existent step (e.g., `color.primary.999`)

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Scenario "Self-check catches broken reference before write"
- **Type:** unit
- **Given:** semantic overrides dict referencing `"color.primary.999"` (step 999 does not exist in global tier)
- **When:** `WC3DTCGFormatter().run(...)` is called
- **Then:** `ValueError` raised with message identifying `{color.primary.999}` as unresolvable
- **File:** `tests/test_dtcg_formatter.py`

#### Test: Output JSON is valid UTF-8 and parseable

- **Maps to:** Requirement "W3C DTCG JSON Serialization" → Acceptance criteria (valid UTF-8 JSON)
- **Type:** unit
- **Given:** standard fixture token dicts
- **When:** formatter writes all output files
- **Then:** each file can be parsed with `json.loads(path.read_text(encoding="utf-8"))` without error
- **File:** `tests/test_dtcg_formatter.py`

---

## Test Coverage Targets

| Metric | Target | Rationale |
|--------|--------|-----------| 
| Line coverage (tools) | ≥80% | PRD quality gate requirement (§8) |
| Branch coverage (tools) | ≥70% | Covers accessibility tier conditionals, density modifier branches, multi-brand paths |
| Line coverage (agent module) | ≥80% | Standard target; integration paths covered by integration test |
| Contrast ratio calculation accuracy | ±0.1 of reference values | WCAG luminance formula validation |
| DTCG self-check: broken references caught | 100% | All reference variants (typo, missing step, non-existent group) must be caught before write |

---

## Test File Inventory

| File | Status | Description |
|------|--------|-------------|
| `tests/test_color_palette_generator.py` | new | ColorPaletteGenerator unit tests (hex anchor, tonal ordering, natural language resolution, lookup table fallback, multi-role, no-color edge case) |
| `tests/test_modular_scale_calculator.py` | new | ModularScaleCalculator unit tests (step values, density modifiers, archetype defaults, scale categories, edge cases) |
| `tests/test_contrast_safe_pairer.py` | new | ContrastSafePairer unit tests (AA/AAA tier selection, WCAG formula accuracy, no-passing-tone edge case, palette immutability) |
| `tests/test_dtcg_formatter.py` | new | WC3DTCGFormatter unit tests (global/semantic tier invariants, self-check, multi-theme `$extensions`, dir creation, multi-brand override files) |
| `tests/test_token_foundation_agent.py` | new | Agent task output tests (file paths, token counts, contrast pairs, multi-brand, integration test with live LLM) |
