# Design: p04-token-foundation-agent

## Technical Approach

P04 implements Agent 2 (Token Foundation Agent) as a CrewAI `Agent` with four deterministic tools, wired as Task T2 in the DS Bootstrap Crew's task chain. It transforms the enriched `BrandProfile` from Agent 1 into three raw W3C DTCG token files on disk: `tokens/base.tokens.json` (global tier), `tokens/semantic.tokens.json` (semantic tier), and `tokens/component.tokens.json` (component-scoped tier). For multi-brand profiles, it additionally writes per-brand semantic override files to `tokens/brands/`.

The agent classifies as Tier 2 (Analytical, Claude Sonnet). Its LLM reasoning layer makes nuanced decisions that fall outside deterministic rules: resolving remaining natural language color descriptions that Agent 1's `_color_notes` could not pin to a specific hex code, choosing palette aesthetics from brand personality values (e.g., applying warm vs. cool undertone bias from the archetype), and reviewing the assembled token set for overall visual coherence before the formatter writes files. The four tools themselves are fully deterministic Python classes.

**Execution flow:**

```
[Task T1 output: enriched BrandProfile (Pydantic)]
  │
  ▼
[TokenFoundationAgent — Task T2]
  ├── 1. ColorPaletteGenerator   ──► global color tokens (palette scales)
  ├── 2. ModularScaleCalculator  ──► global dimension tokens (type, space, radius, shadow, motion)
  ├── 3. ContrastSafePairer      ──► semantic overrides (accessibility-safe aliases)
  └── 4. WC3DTCGFormatter        ──► writes tokens/base.tokens.json
                                      tokens/semantic.tokens.json
                                      tokens/component.tokens.json
                                      tokens/brands/<name>.tokens.json (multi-brand only)
        │
        ▼ TokenFoundationOutput (Pydantic: file_paths, token_counts, contrast_pairs)
  │
  ▼
[Awaits Phase 2: Token Engine Crew]
  └──reads──► tokens/*.tokens.json (raw, pre-validation)
```

## Agent vs. Deterministic Decisions

| Capability | Mode | Rationale |
|------------|------|-----------|
| Tonal scale generation (50–950 steps) | Deterministic (`ColorPaletteGenerator`) | Fixed HSL lightness ladder anchored at step 500 = brand hex; rule-based perceptual shift |
| Natural language color resolution (hex lookup) | Deterministic (lookup table) | Top 300 design color names → hex; used when `_color_notes` provides explicit annotation |
| Ambiguous color intent (personality-driven palette) | Agent (LLM) | Choosing warm vs. cool undertone from archetype and brand personality requires semantic reasoning |
| Typography scale computation | Deterministic (`ModularScaleCalculator`) | Pure math: `baseSize × ratio^n` for each step; no inference needed |
| Spacing scale computation | Deterministic (`ModularScaleCalculator`) | Pure math: fixed multiplier ladder on `baseUnit`; density bias applied by lookup table |
| Elevation, border-radius, opacity, motion scale | Deterministic (`ModularScaleCalculator`) | Archetype-keyed defaults with numeric interpolation |
| WCAG contrast ratio calculation | Deterministic (`ContrastSafePairer`) | Relative luminance formula per WCAG 2.1 spec — pure arithmetic |
| Semantic alias selection (which tone passes contrast) | Deterministic (`ContrastSafePairer`) | Iterate tones 50–950; select highest-contrast passing pair — no judgment needed |
| Token coherence review before write | Agent (LLM) | Final sanity check: does the assembled palette express the brand character stated in the enriched profile? Flags aesthetic anomalies before the file is written. |
| W3C DTCG JSON serialization | Deterministic (`WC3DTCGFormatter`) | Fixed schema: `$value`, `$type`, `$description`, reference syntax `{group.token}` |
| File write to `tokens/` | Deterministic (`WC3DTCGFormatter`) | I/O is pure file system; no inference required |
| Multi-brand override file generation | Deterministic (`WC3DTCGFormatter`) | Set-difference between per-brand overrides and base semantic tokens; deterministic merge |

## Model Tier Assignment

| Agent | Tier | Model | Rationale |
|-------|------|-------|-----------|
| Token Foundation Agent (2) | Tier 2 — Analytical | Claude Sonnet | Makes reasoned color decisions from structured brand inputs; reviews assembled token set for visual coherence. Not generative (produces structured output, not large code artifacts). Matches §3.7 Tier 2 assignment. |

## Architecture Decisions

### Decision: Color tonal scales are purely HSL-space, anchored at step 500

**Context:** Generating color scales from a single brand hex code requires a principled approach. Material Design 3 and Radix Color both use perceptual chroma-linear pipelines, but implementing OKLab or Oklch requires external dependencies and significant complexity.

**Decision:** Use HSL-space with fixed lightness anchors (step 500 = brand color, step 50 = 95% lightness, step 950 = 5% lightness, steps interpolated linearly). Apply a hue-shift of ±5° for light steps and ∓5° for dark steps to create perceptual warmth/coolness that matches archetype personality. Saturation is reduced proportionally at extremes to prevent washed-out or muddy tones.

**Consequences:** The palette is predictable and inspectable from the brand hex code alone. It is not as perceptually uniform as OKLab but is sufficient for design system foundations that the Token Validation Agent (8) will validate for contrast. The validator is the correctness check, not the generator.

### Decision: Semantic tier uses DTCG reference syntax, never raw hex values

**Context:** Semantic tokens represent intent (e.g., `interactive.primary.background`). Hardcoding hex values in the semantic tier would break the architecture: any global token change would require updating semantic tokens too, and the compiled outputs would be one monolithic flat file.

**Decision:** Every semantic token value is a DTCG reference: `"$value": "{color.primary.500}"`. The `WC3DTCGFormatter` enforces this invariant — it processes semantic and component tiers from alias dicts (not value dicts) and raises `ValueError` if a raw hex string appears where a reference is expected.

**Consequences:** The three-tier architecture is enforced in code, not just convention. Token Engine Crew can validate reference integrity using simple recursive resolution. The exit criteria check "Token references resolve" (Fatal §8) is satisfied by construction.

### Decision: ContrastSafePairer selects aliases, does not modify global tones

**Context:** If contrast fails for the required semantic pairs, we have two options: (a) modify the global tone (shift the palette) or (b) choose a different alias in the semantic tier that meets contrast. Option (a) cascades changes across the entire palette, potentially breaking aesthetics. Option (b) is surgical and preserves the palette.

**Decision:** `ContrastSafePairer` only modifies semantic alias selections (which global step is referenced). It never mutates the global tier. If no alias can be found that meets the declared accessibility tier, it logs the highest-contrast available pair as a warning and includes it in `_token_notes`. The Token Validation Agent (8) will catch this in Phase 2 and re-invoke Agent 2 with a structured rejection.

**Consequences:** The global tier is stable and aesthetically consistent. Contrast failures surface as Phase 2 validation rejections — the intended retry path per §3.4. Test cases can assert exact palette output independently of accessibility tier.

### Decision: `WC3DTCGFormatter` runs an internal reference self-check before writing files

**Context:** DTCG reference syntax errors (e.g., `{color.priary.500}` with a typo, or referencing a token that doesn't exist in the global tier) would cause the Token Engine Crew to fail on ingestion. Catching this before file write avoids a needless Phase 2 round-trip.

**Decision:** Before writing, the formatter traverses all `$value` fields in semantic and component tiers that contain `{...}` syntax and resolves them against the assembled global token dict. Any unresolvable reference raises `ValueError` with the token path and the broken reference string.

**Consequences:** `tokens/base.tokens.json` is always self-consistent when written. Reference errors are caught in Phase 1 (T2 task failure → retry at T2 level within DS Bootstrap), not in Phase 2. This reduces cross-phase retry frequency for a common failure mode.

### Decision: Task T2 receives T1's Pydantic output directly via CrewAI task context

**Context:** CrewAI supports task chaining where Task N's output becomes Task N+1's context. The enriched `BrandProfile` Pydantic model from T1 is the exact input Agent 2 needs — including `_color_notes` for natural language color annotations.

**Decision:** Task T2 sets `context=[task_t1]` in its CrewAI Task definition. The task description instructs Agent 2 to parse the T1 output as a `BrandProfile` at the start of its run. This avoids disk I/O for the handoff and keeps the agent chain in-memory within the Crew execution.

**Consequences:** No intermediate file is written between T1 and T2. The `brand-profile.json` on disk is only written after Human Gate approval. If T2 fails, the profile is still in T1's output (in-memory), and T2 can be retried without re-running T1. After Gate approval, `daf generate` writes the profile to disk and calls T2 again with the approved profile (or T2 can be re-run from its saved output).

### Decision: `TokenFoundationOutput` Pydantic model captures file paths and diagnostics

**Context:** The task needs a structured return value for testability and for the First Publish Agent (6) to verify that the expected files exist before handing off to the Token Engine Crew.

**Decision:** Define a `TokenFoundationOutput` Pydantic model with fields: `written_files: list[str]` (absolute paths), `token_counts: dict[str, int]` (per tier), `contrast_pairs: list[ContrastPairResult]` (each pair with ratio and pass/fail), and `token_notes: str | None` (free-form notes from agent reasoning, e.g., "adjusted primary alias to step 700 for AAA compliance"). Task T2 uses `output_pydantic=TokenFoundationOutput`.

**Consequences:** Agent 2's output is always structured and inspectable. The First Publish Agent can assert `len(written_files) == 3` (or `len(written_files) >= 3` for multi-brand) before proceeding. Unit tests can assert exact token counts and contrast ratio values.

## Data Flow

```
[DS Bootstrap Crew — Task T1]
  Brand Discovery Agent (1)
  └──outputs──► enriched BrandProfile (Pydantic, in-memory)
                    │
                    ▼ (CrewAI task context)
[DS Bootstrap Crew — Task T2]
  Token Foundation Agent (2)
  ├── ColorPaletteGenerator   ──► palette: dict[str, str] (global color tokens)
  ├── ModularScaleCalculator  ──► scales: dict[str, Any] (global dimension tokens)
  ├── ContrastSafePairer      ──► overrides: dict[str, str] (semantic alias adjustments)
  └── WC3DTCGFormatter        ──► writes:
        tokens/base.tokens.json        (global tier, ~200–400 tokens)
        tokens/semantic.tokens.json    (semantic tier, ~80–120 tokens)
        tokens/component.tokens.json   (component-scoped tier, ~40–60 tokens)
        tokens/brands/<name>.tokens.json  (multi-brand only, ~10–30 tokens per brand)
  └──outputs──► TokenFoundationOutput (written_files, token_counts, contrast_pairs)
                    │
                    ▼ (file-based handoff to Phase 2)
[Token Engine Crew — Phase 2]
  ├── reads tokens/base.tokens.json
  ├── reads tokens/semantic.tokens.json
  └── reads tokens/component.tokens.json
        │
  [Token Ingestion Agent (7)] ──► normalise + detect duplicates
  [Token Validation Agent (8)] ──► schema, naming, contrast, reference integrity
  [Token Compilation Agent (9)] ──► CSS/SCSS/TS/JSON compiled outputs
  [Token Diff Agent (10)] ──► tokens/diff.json
  [Token Registry Agent (11)] ──► token catalogue metadata
```

```
DS Bootstrap Crew ──writes──► tokens/*.tokens.json (raw) ──reads──► Token Engine Crew
DS Bootstrap Crew ──writes──► brand-profile.json (validated) ──reads──► All 8 downstream crews
```

## Retry & Failure Behavior

**T2-level retry (within DS Bootstrap Crew):**
If `WC3DTCGFormatter` raises `ValueError` (broken reference in self-check), the Task T2 error propagates to CrewAI as a task failure. The Brand Discovery Agent (Agent 1) is NOT re-invoked — only Task T2 is retried. Agent 2 receives the `ValueError` message as context and can adjust its palette or scale decisions before re-running the tools. The DS Bootstrap Crew retries T2 up to **3 times** (matching the per-component retry limit in §3.4).

**Cross-phase retry (T2 ↔ Phase 2 Token Validation Agent 8):**
When the Token Validation Agent (8) rejects the raw token files (naming violations, contrast failures, broken references not caught by T2's self-check), it emits a structured rejection:

```json
{
  "rejected_by": "TokenValidationAgent",
  "failures": [
    { "token": "semantic.interactive.primary.background", "rule": "contrast", 
      "detail": "4.1:1 against surface.default — AA requires 4.5:1" }
  ]
}
```

The First Publish Agent (6) intercepts this rejection, re-invokes Task T2 with the rejection context appended to the task description, and re-runs the Token Engine Crew. The Rollback Agent (40) restores `tokens/` to the pre-T2 checkpoint before each re-run. This loop runs **at most 3 times per token category** (§3.4). If all 3 attempts are exhausted, the pipeline halts with a fatal error listing the unresolved validation failures.

**Non-retry failure modes:**
- `BrandProfile` missing required fields for token generation (e.g., null `colors.primary` and no `_color_notes`) → `ValueError` on T2 start → fatal task error, no retry (Agent 1 should have caught this)
- Disk write failure to `tokens/` → `IOError` propagates → fatal; user must resolve disk issues and re-run

## File Changes

- `src/daf/agents/token_foundation.py` (new) — Token Foundation Agent definition, Task T2 factory, `TokenFoundationOutput` Pydantic model
- `src/daf/tools/color_palette_generator.py` (new) — ColorPaletteGenerator CrewAI BaseTool
- `src/daf/tools/modular_scale_calculator.py` (new) — ModularScaleCalculator CrewAI BaseTool
- `src/daf/tools/contrast_safe_pairer.py` (new) — ContrastSafePairer CrewAI BaseTool
- `src/daf/tools/dtcg_formatter.py` (new) — WC3DTCGFormatter CrewAI BaseTool
- `src/daf/models.py` (modified) — add `TokenFoundationOutput`, `ContrastPairResult` Pydantic models
- `src/daf/agents/brand_discovery.py` (modified) — thread Task T2 into the DS Bootstrap crew task chain (T1 → T2); update Crew definition
- `src/daf/agents/__init__.py` (modified) — export `create_token_foundation_agent`, `create_token_foundation_task`
- `src/daf/tools/__init__.py` (modified) — export the four new tool classes
- `tests/test_token_foundation_agent.py` (new) — agent-level tests (fixtures, output model assertions)
- `tests/test_color_palette_generator.py` (new) — ColorPaletteGenerator unit tests
- `tests/test_modular_scale_calculator.py` (new) — ModularScaleCalculator unit tests
- `tests/test_contrast_safe_pairer.py` (new) — ContrastSafePairer unit tests
- `tests/test_dtcg_formatter.py` (new) — WC3DTCGFormatter unit tests
