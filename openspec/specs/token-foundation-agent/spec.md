# Specification

## Purpose

Behavioral requirements for the Token Foundation Agent (Agent 2, DS Bootstrap Crew) and its four associated tools. This spec covers: color palette generation from brand hex values, modular scale computation for typography and spacing, WCAG contrast-safe semantic alias selection, W3C DTCG three-tier JSON serialization, multi-brand override file generation, Task T2 wiring within the DS Bootstrap Crew, and retry behavior for cross-phase validation failures.

Agent 2 is the first generative agent in the pipeline — it fills the gap between brand intent (from `brand-profile.json`) and the raw token files that the Token Engine Crew (Phase 2) validates and compiles.

---

## Requirements

### Requirement: Color Palette Generation

The `ColorPaletteGenerator` tool MUST generate a complete tonal scale for each semantic color role defined in `BrandProfile.colors`.

#### Acceptance Criteria

- [ ] Generates tonal steps 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950 for each color role
- [ ] Step 500 value equals the exact brand hex code provided in the profile (color anchor)
- [ ] All generated steps are valid `#RRGGBB` hex codes
- [ ] Generates scales for all defined color roles: `primary`, `secondary`, `accent`, `neutral`, `background`, `surface`, `text` (where present in profile)
- [ ] Resolves natural language color descriptions from `_color_notes` to a hex code before scale generation
- [ ] Falls back to a deterministic color lookup table for common color names when `_color_notes` provides no hex annotation
- [ ] Returns a flat dict with keys in the form `color.{role}.{step}` (e.g., `color.primary.500`)
- [ ] Does not call the LLM within the tool — LLM reasoning is delegated to agent layer

#### Scenario: Standard hex color generates full tonal scale

- GIVEN a `BrandProfile` with `colors.primary: "#3D72B4"`
- WHEN `ColorPaletteGenerator` runs
- THEN it returns 11 global-tier tokens: `color.primary.50` through `color.primary.950`
- AND `color.primary.500` equals `"#3D72B4"` (the brand anchor)
- AND all step values are valid `#RRGGBB` hex codes
- AND lighter steps (50–400) have increasing HSL lightness values
- AND darker steps (600–950) have decreasing HSL lightness values

#### Scenario: Natural language color resolved via `_color_notes`

- GIVEN a `BrandProfile` with `colors.primary: "ocean blue"` and `_color_notes: { "colors.primary": "Interpreted as #1E6FA8 — deep professional blue" }`
- WHEN `ColorPaletteGenerator` runs
- THEN it extracts the hex code from `_color_notes` (`#1E6FA8`)
- AND generates the tonal scale anchored at `color.primary.500 = "#1E6FA8"`

#### Scenario: Unresolvable color falls back to lookup table

- GIVEN a `BrandProfile` with `colors.primary: "cerulean"` and `_color_notes` does not contain a hex annotation for this field
- WHEN `ColorPaletteGenerator` runs
- THEN it uses the deterministic color lookup table to resolve `"cerulean"` to its closest match hex
- AND generates the tonal scale from that hex code

#### Scenario: Profile with only primary color defined

- GIVEN a `BrandProfile` with `colors.primary: "#FF5733"` and all other color roles as `None`
- WHEN `ColorPaletteGenerator` runs
- THEN it generates a full scale for `primary` only
- AND returns an empty dict for roles not present in the profile (no phantom tokens)

---

### Requirement: Modular Scale Computation

The `ModularScaleCalculator` tool MUST compute typography, spacing, and supporting scales from the Brand Profile's dimension preferences.

#### Acceptance Criteria

- [ ] Computes 16 typography size steps using: `step_n = baseSize × scaleRatio^n` for `n` in `[-7, 8]`
- [ ] Computes a 12-step spacing ladder from `spacing.baseUnit` (steps 1–12 as integer multiples or ratio-derived values)
- [ ] Applies density modifier: compact = 0.75× multiplier, default = 1×, spacious = 1.33× on spacing steps
- [ ] Computes 6-step elevation scale (CSS `box-shadow` strings) suitable for interface layering
- [ ] Computes 6-step border-radius scale: `none` (0), `sm`, `md`, `lg`, `xl`, `full` (9999px)
- [ ] Computes 10-step opacity scale: 0, 5, 10, 20, 40, 60, 80, 90, 95, 100 (as percent values)
- [ ] Computes 8 motion duration steps: 50, 75, 100, 150, 200, 300, 400, 500 (ms)
- [ ] Computes 5 easing curve definitions: `linear`, `ease-in`, `ease-out`, `ease-in-out`, `spring`
- [ ] Returns all values as a nested dict grouped by category (e.g., `scale.font-size`, `scale.spacing`, `scale.radius`)
- [ ] Uses archetype defaults for any dimension category not specified in the profile

#### Scenario: Enterprise archetype with custom scale ratio

- GIVEN a `BrandProfile` with `archetype: "enterprise-b2b"`, `typography.baseSize: 16`, `typography.scaleRatio: 1.25`, `spacing.baseUnit: 4`
- WHEN `ModularScaleCalculator` runs
- THEN `scale.font-size.base` equals `"16px"` (step 0)
- AND `scale.font-size.lg` equals `"20px"` (≈ `16 × 1.25^1 = 20px`)
- AND `scale.spacing.4` equals `"16px"` (`4 × 4`)
- AND `scale.spacing.8` equals `"32px"` (`4 × 8`)

#### Scenario: Compact density halves effective spacing

- GIVEN a `BrandProfile` with `spacing.density: "compact"` and `spacing.baseUnit: 8`
- WHEN `ModularScaleCalculator` runs
- THEN each spacing step value is approximately 0.75× the default density value for the same step

#### Scenario: Missing typography config uses archetype defaults

- GIVEN a `BrandProfile` with `archetype: "consumer-b2c"` and no `typography` fields set
- WHEN `ModularScaleCalculator` runs
- THEN it applies the `consumer-b2c` archetype defaults (`baseSize: 16`, `scaleRatio: 1.333`)
- AND returns a complete typography scale

---

### Requirement: WCAG Contrast-Safe Semantic Alias Selection

The `ContrastSafePairer` tool MUST select global-tier alias references for mandatory semantic pairings that satisfy the Brand Profile's declared accessibility tier.

#### Acceptance Criteria

- [ ] Evaluates all mandatory semantic pairings: `text.default` on `surface.default`, `text.inverse` on `interactive.primary.background`, `text.inverse` on `interactive.accent.background`
- [ ] Uses the WCAG 2.1 relative luminance formula (no external dependencies) for contrast calculation
- [ ] For AA accessibility tier: all pairings MUST achieve ≥ 4.5:1 contrast ratio for normal-sized text
- [ ] For AAA accessibility tier: all pairings MUST achieve ≥ 7:1 contrast ratio for normal-sized text
- [ ] Selects the alias from the generated palette that meets the threshold with the highest contrast
- [ ] Does NOT modify the global tier palette — only adjusts semantic alias references
- [ ] If no alias achieves the required threshold, logs the closest-passing pair in `contrast_notes` and continues (contrast failure is caught by Token Validation Agent in Phase 2)
- [ ] Returns a `semantic_overrides` dict mapping semantic token names to their selected global-tier alias key

#### Scenario: AA profile selects passing tone for text-on-primary

- GIVEN a palette where `color.primary.500 = "#3D72B4"` (mid-blue) and text-inverse is white-adjacent
- WHEN `ContrastSafePairer` runs with `accessibility = "AA"`
- THEN it evaluates all primary tones against white text
- AND selects a primary tone step where contrast ≥ 4.5:1 (likely step 600 or 700)
- AND returns `{ "interactive.primary.background": "color.primary.700" }` in `semantic_overrides`

#### Scenario: AAA profile selects higher-contrast tone

- GIVEN the same palette as above but `accessibility = "AAA"`
- WHEN `ContrastSafePairer` runs
- THEN it selects a tone with contrast ≥ 7:1 (likely step 800 or 900)
- AND the returned alias step is darker than the AA selection

#### Scenario: No passing tone available (edge case — very light palette)

- GIVEN a very light brand palette where no primary tone achieves 4.5:1 against white
- WHEN `ContrastSafePairer` runs with `accessibility = "AA"`
- THEN it selects the highest-contrast available pair and logs it in `contrast_notes`
- AND does NOT raise an exception
- AND the `ContrastPairResult.passed` flag is `False` for that pair
- AND the Token Foundation Agent includes this in `token_notes` on the output

---

### Requirement: W3C DTCG JSON Serialization

The `WC3DTCGFormatter` tool MUST serialize the assembled token data into three valid W3C DTCG JSON files and write them to the `tokens/` directory.

#### Acceptance Criteria

- [ ] `tokens/base.tokens.json` contains only global-tier tokens with raw `$value` fields (hex, px, ms, etc.)
- [ ] `tokens/semantic.tokens.json` contains only reference-valued tokens (`$value: "{group.token.step}"`) — no raw hex values in the semantic tier
- [ ] `tokens/component.tokens.json` contains component-scoped tokens referencing semantic tokens
- [ ] Every token object has `$value`, `$type`, and `$description` fields
- [ ] Semantic tokens for multi-theme profiles include `$extensions.com.daf.themes` mapping theme mode names to resolved alias references (key MUST be `com.daf.themes` — bare `themes` key is invalid)
- [ ] Raises `ValueError` with the token path and broken reference string if any reference is unresolvable (via `com.daf.themes` self-check pass)
- [ ] All `{...}` reference strings in semantic/component tiers resolve against the global-tier dict before files are written (self-check pass)
- [ ] Raises `ValueError` with the token path and broken reference string if any reference is unresolvable
- [ ] Creates the `tokens/` directory if it does not exist
- [ ] Writes valid UTF-8 JSON (2-space indented for readability)
- [ ] Returns a list of written file paths as strings

#### Scenario: Global tier uses raw values only

- GIVEN a complete palette dict with `color.primary.500 = "#3D72B4"`
- WHEN `WC3DTCGFormatter` runs
- THEN `tokens/base.tokens.json` contains `{ "color": { "primary": { "500": { "$value": "#3D72B4", "$type": "color", "$description": "..." } } } }`
- AND no `$value` field in `base.tokens.json` contains a `{...}` reference string

#### Scenario: Semantic tier uses reference values only

- GIVEN a semantic overrides dict with `interactive.primary.background: "color.primary.700"`
- WHEN `WC3DTCGFormatter` runs
- THEN `tokens/semantic.tokens.json` contains `{ "interactive": { "primary": { "background": { "$value": "{color.primary.700}", "$type": "color", "$description": "..." } } } }`
- AND no `$value` field in `semantic.tokens.json` is a plain hex code

#### Scenario: Self-check catches broken reference before write

- GIVEN a semantic overrides dict where a typo produces reference `{color.priary.700}` (misspelled)
- WHEN `WC3DTCGFormatter` runs
- THEN it raises `ValueError` before writing any file
- AND the error message identifies the token path and the unresolvable reference string

#### Scenario: Multi-theme semantic tokens include `$extensions.com.daf.themes`

- GIVEN a profile with `themes.modes: ["light", "dark"]` and theme-aware semantic alias overrides
- WHEN `WC3DTCGFormatter` runs
- THEN each affected semantic token in `tokens/semantic.tokens.json` includes:
  ```json
  "$extensions": { "com.daf.themes": { "light": "{color.neutral.50}", "dark": "{color.neutral.950}" } }
  ```
- AND using the bare `"themes"` key (without the `com.daf` namespace) raises a `ValueError` before any file is written

---

### Requirement: Multi-Brand Override File Generation

When the Brand Profile specifies `archetype: "multi-brand"` and `themes.brandOverrides: true`, Agent 2 MUST generate per-brand semantic override files.

#### Acceptance Criteria

- [ ] Writes one file per brand name in `themes.brands[]` to `tokens/brands/<brand-name>.tokens.json`
- [ ] Each brand file contains ONLY the semantic tokens that differ from the base semantic tier (not a full copy)
- [ ] All values in brand override files are DTCG reference strings (never raw hex values)
- [ ] Base semantic tier (`tokens/semantic.tokens.json`) remains unchanged — brand overrides are additive/override-only
- [ ] Works for profiles with 1 to N brands (N determined by `themes.brands` array length)

#### Scenario: Two-brand profile generates two override files

- GIVEN a profile with `archetype: "multi-brand"`, `themes.brands: ["brand-a", "brand-b"]`, and distinct primary colors per brand
- WHEN Task T2 completes
- THEN `tokens/brands/brand-a.tokens.json` exists and contains brand-a's semantic token overrides
- AND `tokens/brands/brand-b.tokens.json` exists and contains brand-b's semantic token overrides
- AND `tokens/semantic.tokens.json` contains the neutral base semantic tier
- AND both override files reference only tokens present in `tokens/base.tokens.json`

---

### Requirement: Task T2 Integration in DS Bootstrap Crew

Task T2 (Token Foundation Agent) MUST be wired as a dependent task following Task T1 in the DS Bootstrap Crew's task sequence.

#### Acceptance Criteria

- [ ] Task T2 is defined with `context=[task_t1]` so it receives T1's enriched `BrandProfile` output
- [ ] Task T2 defines `output_pydantic=TokenFoundationOutput` to enforce structured output
- [ ] `TokenFoundationOutput` fields: `written_files: list[str]`, `token_counts: dict[str, int]`, `contrast_pairs: list[ContrastPairResult]`, `token_notes: str | None`
- [ ] Task T2 fails and surfaces an error if T1 has not yet completed (enforced by CrewAI's task dependency mechanism)
- [ ] `daf generate` CLI command's execution log shows T2 starting only after T1's output is available

#### Scenario: T2 runs after T1 completes successfully

- GIVEN `daf generate --profile brand-profile.json --yes` is invoked with a valid profile
- WHEN Task T1 (Brand Discovery Agent) completes with an enriched `BrandProfile`
- THEN Task T2 (Token Foundation Agent) starts automatically
- AND T2 receives the enriched profile including `_color_notes` and `_filled_fields`
- AND T2 completes with a `TokenFoundationOutput` listing at least 3 written files
- AND the three token files exist on disk in the `tokens/` directory

---

### Requirement: Cross-Phase Retry Handling

Task T2 MUST handle structured rejections from the Token Validation Agent (8) in Phase 2 and re-generate token files with corrective context.

#### Acceptance Criteria

- [ ] When Token Validation Agent (8) emits a structured rejection with contrast failures, Agent 2 re-runs with the rejection appended to its task context
- [ ] Agent 2 uses the rejection's `detail` field to identify which semantic alias caused the contrast failure and selects a higher-contrast alternative
- [ ] Re-generated token files overwrite the previous files in `tokens/`
- [ ] The retry counter is tracked and does not exceed 3 attempts per category (per §3.4)
- [ ] If 3 attempts are exhausted without resolution, the pipeline halts with a structured fatal error listing the unresolved validation failures

#### Scenario: Contrast failure triggers T2 retry with corrective context

- GIVEN `tokens/semantic.tokens.json` contains `interactive.primary.background` referencing `color.primary.500` with a 3.9:1 contrast ratio (below AA threshold)
- WHEN Token Validation Agent (8) emits rejection `{ "failures": [{ "token": "interactive.primary.background", "rule": "contrast", "detail": "3.9:1 — AA requires 4.5:1" }] }`
- AND the First Publish Agent (6) re-invokes Task T2 with this rejection as context
- THEN Agent 2 re-runs `ContrastSafePairer` targeting a higher step for `interactive.primary.background`
- AND the new `tokens/semantic.tokens.json` references a step that achieves ≥ 4.5:1 contrast
- AND the retry count increments to 1

#### Scenario: Three failed retries → fatal halt

- GIVEN all three retry attempts for a contrast failure have been exhausted
- WHEN the third attempt still fails Token Validation Agent (8)
- THEN the First Publish Agent (6) halts the pipeline
- AND emits a structured error: `{ "fatal": true, "reason": "T2 retry limit exceeded", "unresolved": [...] }`
- AND the user is shown which token(s) failed and what contrast ratios were achieved
