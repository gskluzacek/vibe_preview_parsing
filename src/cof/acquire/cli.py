"""Command-line interface of the acquire stage (``cof-acquire``)."""

from typing import Annotated

import typer

from cof.acquire import fetch as fetch_mod
from cof.acquire.index import fetch_index
from cof.acquire.listing import fetch_listing
from cof.acquire.manifest import coverage_report, read_manifest, write_manifest
from cof.acquire.params import load_params
from cof.acquire.wayback import WaybackClient
from cof.common.months import month_index
from cof.common.settings import Settings

app = typer.Typer(
    help="Find COF files in the Internet Archive, download them, and verify them.", no_args_is_help=True
)


def _client(settings: Settings) -> WaybackClient:
    """Build an archive client from the settings."""
    return WaybackClient(
        delay=settings.wayback_delay,
        retries=settings.wayback_retries,
        timeout=settings.wayback_timeout,
        user_agent=settings.user_agent,
    )


@app.command()
def index() -> None:
    """Query the archive's capture index (one request per URL pattern); no files are downloaded."""
    settings = Settings()
    client = _client(settings)
    for name, count in fetch_index(client, load_params(settings), settings.acquire_dir).items():
        typer.echo(f"{name:<22} {count:6d} captures")


@app.command()
def listing() -> None:
    """Sample captures of the site's COF listing page and extract the links on them."""
    settings = Settings()
    client = _client(settings)
    for timestamp, count in fetch_listing(
        client, load_params(settings), settings.acquire_dir, settings.listing_every_days
    ):
        typer.echo(f"{timestamp} {count:3d} COF links")


@app.command()
def manifest() -> None:
    """Build manifest.csv from the raw index files."""
    settings = Settings()
    total, plausible, skipped = write_manifest(load_params(settings), settings.acquire_dir)
    typer.echo(f"{total} captures in manifest ({plausible} plausible)")
    typer.echo(f"{skipped} index rows were not single COF files")


@app.command()
def report() -> None:
    """Write and print the per-month coverage report."""
    settings = Settings()
    full, summary = coverage_report(load_params(settings), settings.acquire_dir)
    path = settings.acquire_dir / "report.txt"
    path.write_text(full, encoding="utf-8")
    typer.echo(summary)
    typer.echo(f"full table: {path}")


@app.command(name="all")
def run_all() -> None:
    """Run index, manifest and report in order."""
    index()
    manifest()
    report()


@app.command()
def fetch(
    pilot: Annotated[bool, typer.Option(help="Fetch the pilot set from config/acquire.yaml.")] = False,
    all_months: Annotated[bool, typer.Option("--all", help="Fetch every month in the manifest.")] = False,
    months: Annotated[str | None, typer.Option(help="Comma-separated month codes, e.g. JAN13,AUG10.")] = None,
    kinds: Annotated[str, typer.Option(help="Comma-separated: txt, pdf.")] = "txt,pdf",
    dry_run: Annotated[bool, typer.Option(help="Show what would be fetched.")] = False,
) -> None:
    """Download every distinct version of the chosen months and verify each file."""
    settings = Settings()
    params = load_params(settings)
    captures = read_manifest(settings.acquire_dir)
    wanted_kinds = kinds.split(",")
    if pilot:
        wanted = params.pilot
    elif all_months:
        wanted = sorted(
            {(c.month, k) for c in captures for k in wanted_kinds}, key=lambda t: (month_index(t[0]), t[1])
        )
    elif months:
        wanted = [(m.upper(), k) for m in months.split(",") for k in wanted_kinds]
    else:
        raise typer.BadParameter("give --pilot, --all or --months")
    client = None if dry_run else _client(settings)
    result = fetch_mod.run_fetch(client, captures, settings.originals_dir, wanted, typer.echo, dry_run)
    typer.echo(
        f"{result.considered} files considered, {result.fetched} fetched, "
        f"{len(result.failed)} failed (rerun to retry)"
    )
    for rel in result.failed:
        typer.echo(f"   {rel}")
