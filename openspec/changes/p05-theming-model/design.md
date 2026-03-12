## Context

The DAF pipeline generates a design system with full multi-theme and multi-brand support, as defined in PRD §3.5. Up until this change, the semantics of *how* themes are modelled in DTCG files, how they compile to CSS, and how the generated `ThemeProvider` component switches between them at runtime exist only in the PRD narrative — there is no implementable spec for any of these concerns.

This design covers three tightly coupled but separable problems:
1. **Token structure** — how per-theme values are embedded in W3C DTCG files using `$extensions`
2. **Compilation strategy** — how Style Dictionary reads those extensions and emits per-theme CSS files
3. **Runtime switching** — how the generated `ThemeProvider` React component changes the active theme without touching JavaScript token values

Current state: `WC3DTCGFormatter` tool (Agent 2) already writes `$extensions.themes` on semantic tokens when the brand profile declares multiple themes (see existing spec §Scenario: Multi-theme semantic tokens include `$extensions.themes`). However the key name used is `themes`, not `com.daf.themes`, and the Token Compilation Agent (9) has no spec governing what it does with that extension block.

## Goals / Non-Goals

**Goals:**
- Codify the `com.daf.themes` DTCG extension convention as a formal spec with full acceptance criteria
- Define the Style Dictionary transform pipeline configuration that reads `$extensions.com.daf.themes` and emits one CSS file per theme
- Define the `ThemeProvider` primitive spec — API contract, context shape, initial theme detection, and class-application mechanism
- Define the `useTheme()` hook contract
- Define brand + theme dual-switching: CSS class composition `theme-<name> brand-<name>`
- Update the Token Foundation Agent spec to use `com.daf.themes` (aligned key name)

**Non-Goals:**
- Implementing the Style Dictionary custom transform plugin code (that is agent-generated output, not DAF pipeline source)
- Defining which specific themes (light/dark/high-contrast) are generated — those come from `Brand Profile.themes.modes[]`
- Changing the token tier structure (global/semantic/component) — this change adds metadata inside the existing semantic tier, not a new tier
- Server-side theme rendering (SSR) — out of scope for v1; ThemeProvider is a client component
- Animated theme transitions — CSS transition handling delegated to consumer application

## Decisions

### D1: Extension namespace — `com.daf.themes` over `themes`

**Decision:** Use `$extensions.com.daf.themes` as the extension key for per-theme alias maps in DTCG files.

**Rationale:** The W3C DTCG spec requires vendor-specific extensions to use a reverse-DNS namespace. Using bare `themes` would conflict with any future standardisation of theme support in the DTCG spec. The `com.daf` namespace clearly identifies the owning system and avoids breakage when the DTCG spec evolves.

**Alternative considered:** `x-daf-themes` (common informal practice). Rejected because it violates the DTCG extension spec and signals a temporary rather than deliberate design choice.

**Impact:** The `WC3DTCGFormatter` tool must use `com.daf.themes` not `themes` as the key. The existing spec scenario is updated in the delta spec.

---

### D2: CSS class-scoping over CSS file-swapping

**Decision:** Theme switching applies a `theme-<name>` CSS class to the root element (e.g., `<html class="theme-dark">`). Each CSS file is loaded at page start; only the active class determines which custom properties resolve.

**Rationale:** File-swap approaches (removing/adding `<link>` tags at runtime) cause a flash of unstyled content and require async resource loading. Class-scoping has no FOUC risk, works with SSR hydration, and requires only a single `document.documentElement.classList` mutation.

**Alternative considered:** Importing a single CSS file with `@media (prefers-color-scheme)` blocks. Rejected because it removes programmatic override capability (user cannot override OS preference within the app).

**CSS structure:**
```css
/* variables-base.css — always loaded */
:root { --color-bg-surface: #f5f5f5; }

/* variables-dark.css — always loaded */
.theme-dark { --color-bg-surface: #1a1a1a; }

/* variables-high-contrast.css — always loaded */
.theme-high-contrast { --color-bg-surface: #000000; }
```

All CSS files are bundled into the npm package. The consumer loads them all; `ThemeProvider` controls the active class.

---

### D3: ThemeProvider as a React context provider, not a HOC

**Decision:** `ThemeProvider` is a standard React context provider. `useTheme()` is the consumer hook. No higher-order component pattern.

**Rationale:** Context + hooks is the idiomatic React pattern (React 16.3+). HOC patterns add indirection and are less composable with TypeScript. The generated component library targets React 18+; hooks are the preferred API.

**interface:**
```ts
type Theme = string;   // matches Brand Profile themes.modes[] entry, e.g. "light" | "dark"
type Brand = string;   // matches Brand Profile themes.brands[] entry, e.g. "brand-a"

interface ThemeContextValue {
  theme: Theme;
  brand: Brand | null;
  setTheme: (theme: Theme) => void;
  setBrand: (brand: Brand | null) => void;
  availableThemes: Theme[];
  availableBrands: Brand[];
}
```

---

### D4: Initial theme detection from OS preference

**Decision:** `ThemeProvider` reads `window.matchMedia('(prefers-color-scheme: dark)')` on mount to set the initial theme when no explicit `defaultTheme` prop is provided. Falls back to the first entry in `availableThemes` if the OS result doesn't match a known theme.

**Rationale:** Users expect dark-mode-aware applications. Detecting OS preference without a flash of the wrong theme requires the initial detection to happen synchronously before the first paint (or the `defaultTheme` prop must be set by the consuming application).

**Limitation (accepted):** When SSR is used, the server cannot know the OS preference; the client will correct after hydration. This is acceptable for v1 — SSR support is a non-goal.

---

### D5: Brand override merge — compile-time, not runtime

**Decision:** Brand overrides are merged with base tokens at Style Dictionary compile time, producing separate CSS files per brand. There is no runtime merge of token values.

**Rationale:** Runtime merging would require shipping all brand token data to the browser (privacy concern for white-label scenarios) and would require JavaScript-level token resolution (complexity). Compile-time merge delegates all logic to Style Dictionary and produces flat, self-contained CSS files.

**Trade-off:** Adding a new brand requires a re-run of the Token Engine Crew. This is expected and documented.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `$extensions.com.daf.themes` key mismatch between Agent 2 and Agent 9 | Both agents reference the same compiled theming-model spec. Token Validation Agent (8) validates the key name. |
| CSS class collision if consumer app already uses `theme-*` class names | The generated package documentation MUST warn about class-name collision. Consumers may configure a prefix in `Brand Profile` (future, not this change). |
| `prefers-color-scheme` listener not cleaned up → memory leak in long-lived apps | `ThemeProvider` spec MUST require cleanup of the `MediaQueryList` listener on unmount. |
| Style Dictionary version drift — custom transforms may break on upgrades | Pin Style Dictionary version in the generated package's `package.json`. Token Engine Crew spec (out of scope here) governs version pinning. |
| Brand override files omit unchanged tokens, so diff-based tools see a sparse file | This is intentional by design (D5). Documentation MUST clarify that override files are additive patches, not full replacements. |

## Migration Plan

No user-facing migration is required. This change:
1. Adds new spec files — agents that read them gain new requirements
2. Updates the `token-foundation-agent` spec — aligns the `$extensions` key from `themes` to `com.daf.themes`
3. Adds `ThemeProvider` and `useTheme` as new primitives — no existing component changes

Steps at implementation time:
1. Update `WC3DTCGFormatter` tool to emit `com.daf.themes` key (was `themes`)
2. Implement Style Dictionary transform pipeline configuration per compilation strategy spec
3. Implement `ThemeProvider.tsx` + `useTheme.ts` per primitive spec
4. Update Token Validation Agent (8) to validate `com.daf.themes` block structure
5. Verify all generated CSS files load and class-switching works in a smoke test

**Rollback:** Revert `WC3DTCGFormatter` key name change. CSS files and ThemeProvider are additive new output; removing them is safe.

## Open Questions

- **Q1:** Should `ThemeProvider` support nested scoping (per-subtree theming)? The PRD applies `theme-*` to the root element — design assumes single-root. Nested scoping would require applying the class to a wrapper `<div>` instead. **Decision needed before implementation of ThemeProvider.tsx.**
- **Q2:** Should `Brand Profile` support a custom CSS class prefix to avoid the `theme-*` / `brand-*` collision risk? If yes, this needs to be added to the Brand Profile schema (separate change).
