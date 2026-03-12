"""DAF CLI entry point."""

import json
from pathlib import Path
from typing import Optional

import typer

from daf.validator import validate_profile

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


if __name__ == "__main__":
    app()
