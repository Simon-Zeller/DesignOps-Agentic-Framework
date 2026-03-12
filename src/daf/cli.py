"""DAF CLI entry point."""

import json
from pathlib import Path
from typing import Optional

import typer

from daf.validator import validate_profile
from daf.models import BrandProfile
from daf.agents.brand_discovery import run_brand_discovery

app = typer.Typer(
    name="daf",
    help="DesignOps Agentic Framework CLI — AI-orchestrated design system generation.",
)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """DesignOps Agentic Framework CLI — AI-orchestrated design system generation."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def init(
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        help=(
            "Path to a pre-written Brand Profile JSON file. "
            "Skips the interactive interview and passes the file directly "
            "to the Brand Discovery Agent (§13.5 non-interactive mode)."
        ),
    ),
    resume: Optional[str] = typer.Option(
        None,
        "--resume",
        help=(
            "Path to resume an interrupted run from a saved session file. "
            "Continues from the last completed interview step (§13.1)."
        ),
    ),
) -> None:
    """Initialise a new design system — runs the brand interview and generation pipeline."""
    if profile is not None:
        _load_profile(profile)
        return

    if resume is not None:
        typer.echo(
            f"[daf] Resume mode: resuming from session '{resume}' "
            "(resume logic not yet implemented — coming in P08)."
        )
        return

    # Interactive interview
    from daf.interview import run_interview

    run_interview(cwd=Path.cwd())


def _load_profile(profile_path: str) -> None:
    """Load, validate, and confirm a pre-written brand profile (§13.5)."""
    path = Path(profile_path)

    if not path.exists():
        typer.echo(f"Error: file not found: {profile_path}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        typer.echo(f"Error: could not read profile: {exc}")
        raise typer.Exit(code=1)

    errors = validate_profile(data)
    if errors:
        typer.echo("Validation errors:")
        for err in errors:
            typer.echo(f"  • {err}")
        raise typer.Exit(code=1)

    typer.echo(f"Profile loaded: {profile_path}")
    typer.echo(
        "  Next: pass this profile to the DS Bootstrap Crew (Agent 1)."
    )


# ── daf generate ──────────────────────────────────────────────────────────────


def render_gate_summary(profile: BrandProfile) -> str:
    """Format an enriched BrandProfile as a human-readable summary for the Human Gate.

    Each displayed field is labelled '(default)' if it was filled by ArchetypeResolver,
    or '(specified)' if the user provided it during the interview.
    A 'Warnings' section is appended when consistency findings are present.
    """
    filled = set(profile.filled_fields or [])

    def label(field_path: str) -> str:
        return "(default)" if field_path in filled else "(specified)"

    lines: list[str] = [
        "=" * 54,
        "  Brand Profile Summary",
        "=" * 54,
        f"  Name:            {profile.name}",
        f"  Archetype:       {profile.archetype}",
    ]

    if profile.colors:
        lines.append("")
        lines.append("  Colors:")
        c = profile.colors
        if c.primary is not None:
            lines.append(f"    primary:         {c.primary}  {label('colors.primary')}")
        if c.secondary is not None:
            lines.append(
                f"    secondary:       {c.secondary}  {label('colors.secondary')}"
            )
        if c.accent is not None:
            lines.append(f"    accent:          {c.accent}  {label('colors.accent')}")
        if c.background is not None:
            lines.append(
                f"    background:      {c.background}  {label('colors.background')}"
            )

    if profile.typography:
        lines.append("")
        lines.append("  Typography:")
        t = profile.typography
        if t.scaleRatio is not None:
            lines.append(
                f"    scaleRatio:      {t.scaleRatio}  {label('typography.scaleRatio')}"
            )
        if t.baseSize is not None:
            lines.append(
                f"    baseSize:        {t.baseSize}px  {label('typography.baseSize')}"
            )

    if profile.spacing:
        lines.append("")
        lines.append("  Spacing:")
        s = profile.spacing
        if s.density is not None:
            lines.append(
                f"    density:         {s.density}  {label('spacing.density')}"
            )
        if s.baseUnit is not None:
            lines.append(
                f"    baseUnit:        {s.baseUnit}px  {label('spacing.baseUnit')}"
            )

    if profile.themes:
        lines.append("")
        lines.append("  Themes:")
        th = profile.themes
        if th.modes is not None:
            lines.append(
                f"    modes:           {', '.join(th.modes)}  {label('themes.modes')}"
            )
        if th.brandOverrides is not None:
            lines.append(
                f"    brandOverrides:  {th.brandOverrides}  {label('themes.brandOverrides')}"
            )

    lines.append("")
    _simple: list[tuple[str, str]] = [
        ("borderRadius", "borderRadius"),
        ("elevation", "elevation"),
        ("motion", "motion"),
        ("accessibility", "accessibility"),
        ("componentScope", "componentScope"),
    ]
    for attr, label_text in _simple:
        value = getattr(profile, attr, None)
        if value is not None:
            lines.append(f"  {label_text:<16} {value}  {label(attr)}")

    if profile.breakpoints and profile.breakpoints.strategy is not None:
        lines.append(
            f"  breakpoints      strategy: {profile.breakpoints.strategy}"
            f"  {label('breakpoints.strategy')}"
        )

    if profile.warnings:
        lines.append("")
        lines.append("  Warnings:")
        for w in profile.warnings:
            lines.append(f"    ⚠  {w}")

    lines.append("=" * 54)
    return "\n".join(lines)


@app.command()
def generate(
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        help=(
            "Path to a brand-profile.json file. "
            "Defaults to brand-profile.json in the current directory."
        ),
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Auto-approve the Human Gate prompt (CI/CD mode). Skips interactive review.",
    ),
) -> None:
    """Validate and enrich a brand profile with the Brand Discovery Agent (Agent 1).

    Loads brand-profile.json, runs Agent 1 (Brand Discovery), then prompts for
    Human Gate approval before writing the enriched profile to disk.
    """
    profile_path = Path(profile) if profile else Path.cwd() / "brand-profile.json"

    if not profile_path.exists():
        typer.echo(
            "No brand-profile.json found. Run `daf init` first."
        )
        raise typer.Exit(code=1)

    try:
        raw_profile = json.loads(profile_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        typer.echo(f"Error: could not read profile: {exc}")
        raise typer.Exit(code=1)

    try:
        enriched = run_brand_discovery(raw_profile)
    except ValueError as exc:
        typer.echo(f"Brand discovery failed:\n{exc}")
        raise typer.Exit(code=1)

    if not yes:
        summary = render_gate_summary(enriched)
        typer.echo(summary)
        response = typer.prompt(
            "Approve this brand profile and start generation? [y/N]",
            default="N",
            show_default=False,
        )
        if response.strip().lower() != "y":
            typer.echo(
                "Profile rejected. Edit your answers and re-run `daf init`."
            )
            raise typer.Exit(code=1)

    profile_path.write_text(
        json.dumps(
            enriched.model_dump(by_alias=True, mode="json", exclude_none=True),
            indent=2,
        )
    )
    typer.echo("Brand profile approved and saved.")
    typer.echo(
        "Generation pipeline will be available once Agent 2-6 are wired (P06)."
    )


if __name__ == "__main__":
    app()
