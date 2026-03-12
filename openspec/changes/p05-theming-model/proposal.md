## Why

The DAF pipeline currently produces tokens but has no formal model for how multiple themes (light, dark, high-contrast) and multi-brand overrides are structured, compiled, and switched at runtime. Without a defined theming model, the Token Engine Crew (Phase 2) has no contract to follow when generating per-theme CSS files, and the generated `ThemeProvider` primitive lacks a spec to implement against. This change establishes the complete theming model as an implementable, verifiable system.

## What Changes

- **New**: W3C DTCG `$extensions.com.daf.themes` convention codified as a spec — defines how semantic tokens carry per-theme resolved values
- **New**: `ThemeProvider` primitive spec — CSS-class-based runtime theme switching, exposes `useTheme()` hook with `theme` and `brand` properties
- **New**: `useTheme` hook spec — typed hook contract, `ThemeContext`, initial theme resolution (OS preference via `prefers-color-scheme`)
- **New**: Token compilation strategy spec — per-theme CSS output file naming, class-scoping rules, brand override merge algorithm, and Style Dictionary transform pipeline
- **New**: Multi-brand token file structure codified — `brands/<name>.tokens.json` override files, merge-at-compile-time semantics
- **Modified**: `token-foundation-agent` spec — Token Foundation Agent (2) must now emit the `$extensions.com.daf.themes` block on every semantic token it generates

## Capabilities

### New Capabilities

- `theming-model`: Core theming architecture — DTCG extension convention, per-theme token resolution, CSS class-scoping mechanism, and runtime switching contract
- `theme-provider`: `ThemeProvider` React primitive and `useTheme()` hook — initial theme detection, CSS class application, brand + theme dual switching, context API contract
- `token-compilation-strategy`: Style Dictionary pipeline configuration — per-theme CSS file generation, brand override merge logic, custom transform definitions

### Modified Capabilities

- `token-foundation-agent`: Token Foundation Agent must populate `$extensions.com.daf.themes` on each semantic token using Brand Profile theme list; previously emitted semantic tokens without per-theme values

## Impact

- **Token Engine Crew** (Agents 7–10): Agent 9 (Token Compilation) is directly driven by the compilation strategy spec; Agent 7 (Token Validation) must validate `$extensions.com.daf.themes` blocks; Agent 10 (Token Graph) reference resolution must account for per-theme aliases
- **DS Bootstrap Crew** (Agent 2): Token Foundation Agent spec updated with new per-theme output requirement
- **Design-to-Code Crew**: `ThemeProvider.spec.yaml` provides the source of truth for generating `ThemeProvider.tsx` and `useTheme.ts`
- **Governance Crew**: Token Compliance Agent (32) enforcement rules unchanged — components still consume only semantic tokens; theming model does not alter the component contract
- **Exit criteria**: Fatal check 3 (semantic token references resolve) now applies per-theme alias; no change to check count or severity classification
- **No breaking changes** to existing crew I/O contracts; `tokens/compiled/` output gains additional files, all additive
