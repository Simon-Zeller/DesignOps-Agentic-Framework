# Proposal: p04-token-foundation-agent

## Intent

P03 delivered the Brand Discovery Agent (Agent 1), which produces a validated, fully-specified `brand-profile.json`. That file is rich with brand intent — preferred colors (including natural language descriptions that Agent 1 annotated), typography preferences, spacing density, accessibility tier, scope, and theme mode requirements — but it is still brand *intent*, not a design system *token store*.

Without Agent 2, there is no mechanism to translate the enriched Brand Profile into the three-tier W3C DTCG token files that every downstream crew depends on. The Token Engine Crew (Phase 2) cannot validate without raw tokens. The Design-to-Code Crew (Phase 3) cannot generate components without compiled token references. The entire generation pipeline is blocked at the Phase 1/Phase 2 boundary until the raw token files exist on disk.

P04 implements **Agent 2: Token Foundation Agent** of the DS Bootstrap Crew. This is the creative generation step — it synthesizes a complete, harmonious, contrast-safe initial token set in all three tiers and writes it to `tokens/`. It completes Task T2 and makes the raw token I/O contract between DS Bootstrap and Token Engine operational for the first time.

## Scope

### In scope

- **Agent 2: Token Foundation Agent** — CrewAI `Agent` with role, goal, backstory, and tool assignments (§4.1)
- **Color Palette Generator tool** — derives a complete primitive color palette from the Brand Profile's color fields. Resolves natural language color annotations from `_color_notes` (left by Agent 1) to hex values. Generates full tonal scales (50–950) for primary, secondary, accent, neutral, background, surface, and text using perceptual hue-shifting. Produces global-tier color tokens.
- **Modular Scale Calculator tool** — computes a typography scale (font-size step sequence) and spacing scale from `typography.scaleRatio`, `typography.baseSize`, and `spacing.baseUnit`. Generates the full step ladder (e.g., `size-1` through `size-16`) in both px and rem. Also computes elevation (shadow) scale, border-radius scale, opacity scale, and motion/easing curves from archetype-appropriate defaults where the Brand Profile does not specify.
- **Contrast-Safe Pairer tool** — evaluates all foreground/background color pairings against WCAG 2.1 contrast ratios (AA = 4.5:1 for normal text, AAA = 7:1 for the AAA tier). Adjusts semantic token mappings so that text-on-surface, text-on-primary, and text-on-accent pairs satisfy the Brand Profile's `accessibility` tier. Does not modify global tones — adjusts semantic-tier alias references to select a passing tone from the palette.
- **W3C DTCG Formatter tool** — serializes the token data structures to valid W3C DTCG JSON (each token as `{ "$value": ..., "$type": ..., "$description": ... }`). Enforces three-tier separation: global tokens use raw values, semantic tokens use `{group.token}` references to global tokens, component-scoped tokens use `{semantic.token}` references. Writes the three output files.
- **Multi-brand support** — when `archetype: multi-brand` and `themes.brandOverrides: true`, generate the `tokens/brands/` directory with per-brand semantic override files (one file per brand name from `themes.brands[]`). Each override file contains only the semantic tokens that differ from the base semantic tier.
- **`tokens/` output** — `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, `tokens/component.tokens.json` (all raw, pre-validation). Multi-brand: also `tokens/brands/<brand-name>.tokens.json` per brand.
- **Wire Task T2** in the DS Bootstrap Crew's task chain — after Task T1 (Brand Discovery Agent) completes, Task T2 receives the enriched `BrandProfile` and invokes Agent 2
- **Unit tests** for all four tools and for the agent task output fixture

### Out of scope

- Token validation and WCAG contrast audit by the Token Engine Crew — that is Phase 2 (Token Engine Crew, Agents 7–11); Agent 2 makes a best-effort contrast-safe selection but does NOT replace Phase 2 validation
- Token compilation to CSS / SCSS / TypeScript / JSON flat — that is the Token Compilation Agent (9) in Phase 2
- `tokens/diff.json` — produced by the Token Engine Crew after validation, not by Agent 2
- Primitive spec YAMLs (`specs/*.spec.yaml`) — Task T3 (Primitive Scaffolding Agent, Agent 3), a subsequent change
- Component spec YAMLs — Task T4 (Core Component Agent, Agent 4), a subsequent change
- `pipeline-config.json` and project scaffolding files — Task T5 (Pipeline Configuration Agent, Agent 5), a subsequent change
- Triggering the Token Engine Crew or any Phase 2 work — that is the First Publish Agent (6), a later change
- Resume-from-checkpoint (`--resume` flag) — P08
- Token schema evolution for delta updates (ADDED/MODIFIED/REMOVED sections) — a future governance change

## Affected Crews & Agents

| Crew | Agent(s) | Impact |
|------|----------|--------|
| DS Bootstrap (Crew 1) | Agent 2: Token Foundation Agent | **Implemented here.** Role, goal, backstory, tools, and task T2 are all new. |
| DS Bootstrap (Crew 1) | Agent 1: Brand Discovery Agent | **Upstream.** Agent 2 reads the enriched `BrandProfile` output from Agent 1, including `_color_notes`. No behavioral change to Agent 1, but the T2 task wiring is added. |
| DS Bootstrap (Crew 1) | Agent 6: First Publish Agent | **Downstream.** The raw token files written here are the I/O contract that P06 will hand off to the Token Engine Crew. The file paths and DTCG structure established in P04 define that contract. |
| Token Engine (Crew 2) | Agent 7: Token Ingestion Agent | **Downstream.** Receives `tokens/base.tokens.json`, `tokens/semantic.tokens.json`, `tokens/component.tokens.json` from this agent. The naming, format, and three-tier reference structure established here is the input contract for Phase 2. |
| Token Engine (Crew 2) | Agent 8: Token Validation Agent | **Retry partner.** When Phase 2 validation fails, the Token Foundation Agent is re-invoked with structured rejection context (§3.4 cross-phase retry). This retry hook is established by P04. |

## PRD References

- **§4.1 DS Bootstrap Crew — Agent 2** — Role, goal, tools, input/output specification, and Task T2 definition
- **§3.2 Token Architecture** — W3C DTCG three-tier structure (global, semantic, component-scoped); theme support via `$extensions` on semantic tokens
- **§3.6 Crew I/O Contracts** — DS Bootstrap writes raw `tokens/*.tokens.json`; Token Engine reads and validates them
- **§3.4 Retry Protocol** — Token Foundation Agent (2) ↔ Token Validation Agent (8) cross-phase retry pair; max 3 retries per component
- **§3.7 Model Assignment Strategy** — Agent 2 is Tier 2 (Claude Sonnet): analytical, makes reasoned color and scale decisions from structured input
- **§2.3 Output Structure** — defines the exact file paths under `tokens/` (base, semantic, component, compiled/, diff) and the multi-brand `tokens/brands/` structure
- **§3.3 Multi-Brand / Theme Architecture** — `ThemeProvider` contract, semantic token per-theme values via `$extensions`, brand override files structure

## Pipeline Impact

- [ ] Pipeline phase ordering
- [x] Crew I/O contracts (§3.6) — establishes the raw `tokens/*.tokens.json` files written by DS Bootstrap and consumed by the Token Engine Crew; the first time this file-based handoff is implemented in code
- [ ] Retry protocol (§3.4) — the retry *pair* (Agent 2 ↔ Agent 8) is established here but the invocation mechanism lives in Agent 6 (P06)
- [ ] Human gate policy (§5)
- [ ] Exit criteria (§8)
- [ ] Brand Profile schema (§6)

## Approach

1. **Implement `ColorPaletteGenerator` tool** — accepts the `BrandProfile.colors` dict and `_color_notes` annotation. Resolves any non-hex color description to a hex code using the Claude annotation already present in `_color_notes` (if not resolvable deterministically, uses a lookup table of common design system colors as fallback). Generates 10-step tonal scales (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950) for each semantic color role using an HSL-space lightness ladder with perceptual adjustments. Returns a flat dict of `{ "color.{role}.{step}": hex }` pairs suitable for the global tier.

2. **Implement `ModularScaleCalculator` tool** — accepts `typography.scaleRatio`, `typography.baseSize`, and `spacing.baseUnit` from the profile. Computes 16 typography steps centered on `baseSize` using the ratio. Computes a 12-step spacing ladder (4px–192px for a base-8 grid, scaled proportionally for compact/spacious density). Also produces a 6-step elevation scale (shadow CSS values with blur/spread progressions), a 6-step border-radius scale (from sharp to pill), an opacity scale (0, 5, 10, 20, 40, 60, 80, 90, 95, 100), motion duration steps (50ms–500ms), and standard easing curves. Returns a structured dict per token category.

3. **Implement `ContrastSafePairer` tool** — built on the WCAG 2.1 relative luminance formula (no external dependencies). Iterates over the semantic pairings that must pass (text/surface, text-inverse/primary, text-inverse/accent) and selects the highest-contrast foreground tone from the generated palette that meets the accessibility tier threshold (AA or AAA). Returns a `semantic_overrides` dict that the DTCG Formatter uses when mapping global→semantic aliases.

4. **Implement `WC3DTCGFormatter` tool** — accepts the three dicts (global palette, scale tokens, semantic overrides) and serializes them as valid W3C DTCG JSON. Global tier: raw values (`$value`) with `$type` and `$description`. Semantic tier: reference aliases (`$value: "{color.primary.500}"`) plus `$extensions.themes` object mapping each theme mode to its resolved alias. Component tier: component-scoped overrides using semantic references. For multi-brand: writes per-brand `$extensions.brands` entries where overrides exist. Writes to `tokens/` directory, creating it if absent.

5. **Define `TokenFoundationAgent`** — `Agent(role=..., goal=..., backstory=..., tools=[...], llm=tier2_model)`. Task T2 receives the enriched `BrandProfile` pydantic output from Task T1 and runs the four tools in sequence: ColorPaletteGenerator → ModularScaleCalculator → ContrastSafePairer → WC3DTCGFormatter. Returns a `TokenFoundationOutput` pydantic model listing the three output file paths and a summary of token counts per category.

6. **Wire Task T2 in crew task chain** — update `src/daf/agents/brand_discovery.py` (or create a DS Bootstrap Crew module) to chain T1 → T2. Task T2 receives T1's `output_pydantic` as its input via CrewAI's task context mechanism.

7. **Unit tests** — test each tool in isolation with representative inputs (valid Brand Profile fixture, edge cases for missing fields, AAA vs AA accessibility tiers, multi-brand profile, natural-language color in `_color_notes`). Test the agent task output with a fixture asserting that all three DTCG files are written and structurally valid. Test that all semantic pairings pass the declared accessibility tier.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Natural language color resolution produces incorrect hex values | Medium | Agent 1 already annotates `_color_notes` with its interpretation; Agent 2 trusts this annotation. Provide a deterministic fallback lookup table for the 20 most common design color names so the LLM is not invoked during tool execution. |
| Tonal scale generation produces visually inconsistent palettes | Low | Use HSL-space with fixed lightness anchors (e.g., step 500 = brand hex, steps 50/950 approach 95%/5% lightness); perceptual adjustments are rule-based, not LLM-generated. Standard pattern established by Material Design and Radix. |
| WCAG contrast pairer selects a tone that passes numerically but looks wrong | Low | Log the selected tone and its contrast ratio in `_token_notes` on the output. The Token Validation Agent (Phase 2, Agent 8) performs an independent contrast audit and will flag issues before compilation. |
| Multi-brand semantics token files grow too large for context window | Low | Brand override files contain ONLY differing semantic tokens — the delta is small (typically 10–20 tokens per brand for a typical brand palette swap). |
| DTCG reference syntax errors cause Phase 2 validation failures | Medium | WC3DTCGFormatter uses a fixed reference template `{group.subgroup.step}` with strict interpolation — no string concatenation. Add a self-check pass in the formatter that resolves all `{}` references against the global tier before writing files. |
