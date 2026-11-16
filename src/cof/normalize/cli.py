"""Command-line interface of the normalize stage (``cof-normalize``)."""

from pathlib import Path
from typing import Annotated

import typer

from cof.common.settings import Settings
from cof.normalize.context import build_context
from cof.normalize.pipeline import run_pipeline
from cof.normalize.rules import detect_all, load_rules

app = typer.Typer(help="Normalize the selected COF text files.", no_args_is_help=True)


@app.command()
def run(
    months: Annotated[str | None, typer.Option(help="Comma-separated month codes, e.g. JAN13,AUG10.")] = None,
) -> None:
    """Normalize every selected text file (or only the given months) and write the reports."""
    wanted = {m.strip().upper() for m in months.split(",")} if months else None
    run_pipeline(Settings(), wanted, typer.echo)


@app.command()
def detect(
    path: Annotated[Path, typer.Argument(help="A COF text file.")],
    month: Annotated[str, typer.Option(help="Month code of the file, e.g. JAN13.")],
) -> None:
    """Report the issues found in one file without changing anything."""
    rules = load_rules(Settings())
    for issue in detect_all(build_context(month.upper(), path.read_bytes())):
        rule = rules[issue.rule_id]
        where = issue.line or "-"
        typer.echo(f"{issue.rule_id} {rule.rule_class:<13} line {where:>5}  {rule.name}: {issue.evidence}")
