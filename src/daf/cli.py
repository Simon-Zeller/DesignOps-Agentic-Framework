"""DAF CLI entry point."""

from typing import Optional

import typer

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
        typer.echo(
            f"[daf] Profile mode: loading brand profile from '{profile}' "
            "(interview skipped — not yet implemented, wired up in P02)."
        )
        return

    if resume is not None:
        typer.echo(
            f"[daf] Resume mode: resuming from session '{resume}' "
            "(resume logic not yet implemented, wired up in P02)."
        )
        return

    typer.echo(
        "[daf] Interactive interview: the 11-step brand interview "
        "is not yet implemented (coming in P02)."
    )


if __name__ == "__main__":
    app()
