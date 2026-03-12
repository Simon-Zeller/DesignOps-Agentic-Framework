"""11-step brand interview CLI runner for DAF.

Orchestrates the interactive brand profile interview, persists session
state after each step, validates the assembled profile, and writes
``brand-profile.json`` to the current working directory.

No LLM is called here.  Natural language color descriptions are stored
verbatim — resolution to hex is done by the Brand Discovery Agent (P03).
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import typer

from daf.archetypes import ARCHETYPE_DEFAULTS
from daf.session import SessionManager
from daf.validator import validate_profile

ARCHETYPES = [
    "enterprise-b2b",
    "consumer-b2c",
    "mobile-first",
    "multi-brand",
    "custom",
]

ARCHETYPE_LABELS = {
    "enterprise-b2b": "Professional, data-dense B2B enterprise",
    "consumer-b2c": "Consumer-facing, engaging and visual",
    "mobile-first": "Mobile-optimised, touch-friendly",
    "multi-brand": "Multi-brand platform, flexible tokens",
    "custom": "Custom — start with minimal defaults",
}

_COMPONENT_OVERRIDES_TEMPLATE = """{
  "Button": {
    "borderRadius": "4px",
    "fontWeight": "600"
  },
  "Card": {
    "borderRadius": "8px",
    "elevation": "2"
  }
}
"""


@dataclass
class InterviewState:
    # Step 1 — required
    name: str = ""
    # Step 2 — required
    archetype: str = ""
    # Step 3 — colors
    colors_primary: str = ""
    colors_secondary: str = ""
    colors_neutral: str = ""
    colors_semantic_success: str = ""
    colors_semantic_warning: str = ""
    colors_semantic_error: str = ""
    colors_semantic_info: str = ""
    # Step 4 — typography
    typography_scale_ratio: float = 1.25
    typography_base_size: int = 16
    # Step 5 — spacing
    spacing_density: str = "default"
    # Step 6 — border radius
    border_radius: str = "md"
    # Step 7 — elevation
    elevation: str = "default"
    # Step 8 — motion
    motion: str = "default"
    # Step 9 — themes
    themes: str = "light,dark"
    # Step 10 — accessibility
    accessibility: str = "AA"
    # Step 11 — component scope + overrides
    component_scope: str = "standard"
    component_overrides: Optional[dict[str, Any]] = field(default=None)
    # Session tracking
    last_step: int = 0


def build_profile(state: InterviewState) -> dict[str, Any]:
    """Assemble a §6-conformant brand profile dict from *state*."""
    from daf.archetypes import ARCHETYPE_DEFAULTS

    archetype_defaults = ARCHETYPE_DEFAULTS.get(state.archetype, {})
    breakpoints = archetype_defaults.get(
        "breakpoints",
        {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"},
    )

    profile: dict[str, Any] = {
        "name": state.name,
        "archetype": state.archetype,
        "colors": {
            "primary": state.colors_primary,
            "secondary": state.colors_secondary,
            "neutral": state.colors_neutral,
            "semantic": {
                "success": state.colors_semantic_success,
                "warning": state.colors_semantic_warning,
                "error": state.colors_semantic_error,
                "info": state.colors_semantic_info,
            },
        },
        "typography": {
            "scaleRatio": state.typography_scale_ratio,
            "baseSize": state.typography_base_size,
        },
        "spacing": {"density": state.spacing_density},
        "borderRadius": state.border_radius,
        "elevation": state.elevation,
        "motion": state.motion,
        "themes": [t.strip() for t in state.themes.split(",") if t.strip()],
        "accessibility": state.accessibility,
        "componentScope": state.component_scope,
        "breakpoints": breakpoints,
    }

    if state.component_overrides is not None:
        profile["componentOverrides"] = state.component_overrides

    return profile


def collect_overrides() -> Optional[dict[str, Any]]:
    """Attempt to collect component overrides via ``$EDITOR``.

    Returns the parsed override dict, or None if the editor is not
    available or the user skips.
    """
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        typer.echo(
            "No editor configured (set $EDITOR to add overrides)."
            " Skipping component overrides."
        )
        return None

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="daf-overrides-"
    ) as tmp:
        tmp.write(_COMPONENT_OVERRIDES_TEMPLATE)
        tmp_path_str = tmp.name

    try:
        subprocess.run([editor, tmp_path_str], check=True)  # noqa: S603
    except (subprocess.CalledProcessError, FileNotFoundError):
        typer.echo("Editor exited with an error. Skipping component overrides.")
        Path(tmp_path_str).unlink(missing_ok=True)
        return None

    try:
        content = Path(tmp_path_str).read_text()
        parsed: Any = json.loads(content)
        if not isinstance(parsed, dict):
            typer.echo("Invalid JSON (expected object). Skipping component overrides.")
            return None
        result: dict[str, Any] = parsed
        return result
    except (json.JSONDecodeError, OSError):
        typer.echo("Could not parse overrides JSON. Skipping component overrides.")
        return None
    finally:
        Path(tmp_path_str).unlink(missing_ok=True)


def _apply_archetype_defaults(state: InterviewState) -> None:
    """Populate *state* optional-field slots from archetype defaults."""
    defaults = ARCHETYPE_DEFAULTS.get(state.archetype, {})
    colors = defaults.get("colors", {})
    semantic = colors.get("semantic", {})
    typography = defaults.get("typography", {})
    spacing = defaults.get("spacing", {})

    state.colors_primary = colors.get("primary", state.colors_primary)
    state.colors_secondary = colors.get("secondary", state.colors_secondary)
    state.colors_neutral = colors.get("neutral", state.colors_neutral)
    state.colors_semantic_success = semantic.get("success", state.colors_semantic_success)
    state.colors_semantic_warning = semantic.get("warning", state.colors_semantic_warning)
    state.colors_semantic_error = semantic.get("error", state.colors_semantic_error)
    state.colors_semantic_info = semantic.get("info", state.colors_semantic_info)
    state.typography_scale_ratio = float(
        typography.get("scaleRatio", state.typography_scale_ratio)
    )
    state.typography_base_size = int(
        typography.get("baseSize", state.typography_base_size)
    )
    state.spacing_density = spacing.get("density", state.spacing_density)
    state.border_radius = defaults.get("borderRadius", state.border_radius)
    state.elevation = defaults.get("elevation", state.elevation)
    state.motion = defaults.get("motion", state.motion)
    raw_themes = defaults.get("themes", ["light", "dark"])
    if isinstance(raw_themes, list):
        state.themes = ",".join(raw_themes)
    state.accessibility = defaults.get("accessibility", state.accessibility)
    state.component_scope = defaults.get("componentScope", state.component_scope)


def _save_step(step_num: int, state: InterviewState, session: SessionManager) -> None:
    """Update state.last_step and persist to session file."""
    state.last_step = step_num
    session.save(state.last_step, _state_to_dict(state))


def _step1_name(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 1/11] Project name *")
    while True:
        name: Any = typer.prompt("  Project name", default=state.name or None, prompt_suffix=": ")
        if name and str(name).strip():
            state.name = str(name).strip()
            _save_step(1, state, session)
            return
        typer.echo("  ✗ Project name is required.")


def _step2_archetype(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 2/11] Archetype *")
    for i, archetype in enumerate(ARCHETYPES, start=1):
        typer.echo(f"  {i}. {archetype:<20} — {ARCHETYPE_LABELS[archetype]}")

    while True:
        choice = typer.prompt("  Select archetype [1-5]", prompt_suffix=": ")
        try:
            idx = int(choice.strip()) - 1
            if 0 <= idx < len(ARCHETYPES):
                state.archetype = ARCHETYPES[idx]
                _apply_archetype_defaults(state)
                _save_step(2, state, session)
                return
        except ValueError:
            pass
        typer.echo("  ✗ Please enter a number between 1 and 5.")


def _prompt_color(prompt: str, default: str) -> str:
    """Prompt for a color value with the archetype default shown."""
    while True:
        raw: Any = typer.prompt(f"  {prompt}", default=default, prompt_suffix=": ")
        value = str(raw) if raw else default
        if not value:
            return default
        # Validate inline: start with # → must be valid hex; single-word non-# → error
        from daf.validator import _is_valid_hex, _is_natural_language

        if value.startswith("#"):
            if _is_valid_hex(value):
                return value
            typer.echo(
                "  ✗ Invalid hex color — must be 3 or 6 hex digits (e.g., #FF0000)."
            )
        elif _is_natural_language(value):
            return value  # accepted verbatim as natural language description
        else:
            typer.echo(
                "  ✗ Invalid color value — use a hex code (#RRGGBB) or"
                " a natural language description (e.g., 'a warm coral red')."
            )


def _step3_colors(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 3/11] Brand colors  (Enter to accept default)")
    state.colors_primary = _prompt_color("Primary color", state.colors_primary)
    state.colors_secondary = _prompt_color("Secondary color", state.colors_secondary)
    state.colors_neutral = _prompt_color("Neutral color", state.colors_neutral)
    typer.echo("  Semantic colors:")
    state.colors_semantic_success = _prompt_color("  Success", state.colors_semantic_success)
    state.colors_semantic_warning = _prompt_color("  Warning", state.colors_semantic_warning)
    state.colors_semantic_error = _prompt_color("  Error", state.colors_semantic_error)
    state.colors_semantic_info = _prompt_color("  Info", state.colors_semantic_info)
    _save_step(3, state, session)


def _step4_typography(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 4/11] Typography  (Enter to accept default)")
    while True:
        ratio_str = typer.prompt(
            "  Scale ratio (1.0–2.0)",
            default=str(state.typography_scale_ratio),
            prompt_suffix=": ",
        )
        try:
            ratio = float(ratio_str)
            if 1.0 <= ratio <= 2.0:
                state.typography_scale_ratio = ratio
                break
            typer.echo("  ✗ Scale ratio must be between 1.0 and 2.0.")
        except ValueError:
            typer.echo("  ✗ Please enter a number (e.g., 1.25).")

    while True:
        size_str = typer.prompt(
            "  Base size px (8–24)",
            default=str(state.typography_base_size),
            prompt_suffix=": ",
        )
        try:
            size = int(size_str)
            if 8 <= size <= 24:
                state.typography_base_size = size
                break
            typer.echo("  ✗ Base size must be between 8 and 24.")
        except ValueError:
            typer.echo("  ✗ Please enter an integer.")

    _save_step(4, state, session)


def _step5_spacing(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 5/11] Spacing density  (Enter to accept default)")
    density = typer.prompt(
        "  Density [compact/default/comfortable]",
        default=state.spacing_density,
        prompt_suffix=": ",
    )
    state.spacing_density = density.strip() or state.spacing_density
    _save_step(5, state, session)


def _step6_border_radius(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 6/11] Border radius  (Enter to accept default)")
    radius = typer.prompt(
        "  Border radius [none/sm/md/lg/full]",
        default=state.border_radius,
        prompt_suffix=": ",
    )
    state.border_radius = radius.strip() or state.border_radius
    _save_step(6, state, session)


def _step7_elevation(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 7/11] Elevation style  (Enter to accept default)")
    elevation = typer.prompt(
        "  Elevation [flat/subtle/default/material/expressive]",
        default=state.elevation,
        prompt_suffix=": ",
    )
    state.elevation = elevation.strip() or state.elevation
    _save_step(7, state, session)


def _step8_motion(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 8/11] Motion preset  (Enter to accept default)")
    motion = typer.prompt(
        "  Motion [none/reduced/default/lively]",
        default=state.motion,
        prompt_suffix=": ",
    )
    state.motion = motion.strip() or state.motion
    _save_step(8, state, session)


def _step9_themes(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 9/11] Color themes  (Enter to accept default)")
    themes = typer.prompt(
        "  Themes (comma-separated, e.g. light,dark)",
        default=state.themes,
        prompt_suffix=": ",
    )
    state.themes = themes.strip() or state.themes
    _save_step(9, state, session)


def _step10_accessibility(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 10/11] Accessibility target  (Enter to accept default)")
    level = typer.prompt(
        "  Accessibility level [AA/AAA]",
        default=state.accessibility,
        prompt_suffix=": ",
    )
    state.accessibility = level.strip() or state.accessibility
    _save_step(10, state, session)


def _step11_components(state: InterviewState, session: SessionManager) -> None:
    typer.echo("\n[Step 11/11] Component configuration  (Enter to accept default)")
    scope = typer.prompt(
        "  Component scope [minimal/standard/comprehensive]",
        default=state.component_scope,
        prompt_suffix=": ",
    )
    state.component_scope = scope.strip() or state.component_scope

    add_overrides = typer.prompt(
        "  Add component overrides? (y/N)",
        default="N",
        prompt_suffix=": ",
    )
    if add_overrides.strip().lower() == "y":
        state.component_overrides = collect_overrides()
    else:
        state.component_overrides = None

    _save_step(11, state, session)


_STEPS = [
    _step1_name,
    _step2_archetype,
    _step3_colors,
    _step4_typography,
    _step5_spacing,
    _step6_border_radius,
    _step7_elevation,
    _step8_motion,
    _step9_themes,
    _step10_accessibility,
    _step11_components,
]


def _state_to_dict(state: InterviewState) -> dict[str, Any]:
    d: dict[str, Any] = state.__dict__.copy()
    return d


def _state_from_dict(data: dict[str, Any]) -> InterviewState:
    state = InterviewState()
    for key, val in data.items():
        if hasattr(state, key):
            setattr(state, key, val)
    return state


def run_interview(cwd: Optional[Path] = None) -> dict[str, Any]:
    """Run the 11-step brand interview and return the assembled profile dict.

    Writes ``brand-profile.json`` in *cwd* (defaults to ``Path.cwd()``).
    Deletes ``.daf-session.json`` on successful completion.
    """
    effective_cwd = Path(cwd) if cwd is not None else Path.cwd()
    session = SessionManager(cwd=effective_cwd)
    state = InterviewState()
    start_step = 0

    # --- Session resume check ---
    saved = session.load()
    if saved is not None:
        last = saved.get("last_step", 0)
        resume = typer.prompt(
            f"\nResume from step {last + 1} (y) or start over (n)?",
            default="y",
            prompt_suffix=" ",
        )
        if resume.strip().lower() in ("y", "yes", ""):
            state = _state_from_dict(saved.get("answers", {}))
            state.last_step = last
            start_step = last
            typer.echo(f"Resuming from step {start_step + 1}…")
        else:
            session.delete()

    typer.echo("\n" + "=" * 60)
    typer.echo("  DAF Brand Interview")
    typer.echo("=" * 60)

    for i, step_fn in enumerate(_STEPS):
        step_num = i + 1
        if step_num <= start_step:
            continue  # already completed
        step_fn(state, session)

    # --- Validate ---
    profile = build_profile(state)
    errors = validate_profile(profile)
    if errors:
        typer.echo("\n✗ Profile validation failed:")
        for err in errors:
            typer.echo(f"  • {err}")
        raise typer.Exit(code=1)

    # --- Write output ---
    output_path = effective_cwd / "brand-profile.json"
    output_path.write_text(json.dumps(profile, indent=2))
    session.delete()

    typer.echo(f"\n✓ Brand profile written to {output_path}")
    typer.echo(
        "  Next: run the DS Bootstrap Crew to generate your design system."
    )

    return profile
