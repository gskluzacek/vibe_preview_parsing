"""Ad-hoc: make ``data/pdf/YYYY_MM.pdf`` symbolic links to the selected PDF of each month.

Run by hand::

    uv run python adhoc/link_pdfs.py

Reads ``<originals>/selection.csv`` (see ``select_versions.py``) and creates one relative symbolic link per
month, named like the normalized files, pointing at the version marked ``selected`` or ``only_version``.
Months with several PDF versions therefore get exactly one link. Existing links are replaced, links for
months that are no longer selected are removed, and anything that is not a link is left alone. A selected
PDF that has no ``%%EOF`` marker (truncated at download) is still linked, but listed in the report.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import typer

from cof.common.csvio import read_rows
from cof.common.months import month_index, to_period
from cof.common.settings import Settings

_TAIL_BYTES = 2048


@dataclass
class LinkReport:
    """What a run did."""

    linked: list[str] = field(default_factory=list)  # periods linked
    truncated: list[str] = field(default_factory=list)  # linked, but the PDF has no %%EOF
    removed: list[str] = field(default_factory=list)  # stale links deleted
    missing_file: list[str] = field(default_factory=list)  # selected, but the file is not on disk


def has_eof_marker(path: Path) -> bool:
    """Tell whether a PDF ends with the ``%%EOF`` marker (a truncated download does not)."""
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        handle.seek(max(0, handle.tell() - _TAIL_BYTES))
        return b"%%EOF" in handle.read()


def link_pdfs(originals_dir: Path, links_dir: Path) -> LinkReport:
    """Create the ``YYYY_MM.pdf`` links for every month with a selected PDF.

    Args:
        originals_dir: Directory holding ``selection.csv`` and the downloaded files.
        links_dir: Directory to put the links in (created if needed).

    Returns:
        The periods linked, flagged as truncated, removed or missing.
    """
    report = LinkReport()
    chosen = {
        r["month"]: r
        for r in read_rows(originals_dir / "selection.csv")
        if r["kind"] == "pdf" and r["status"] in ("selected", "only_version")
    }
    links_dir.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    for month in sorted(chosen, key=month_index):
        source = originals_dir / chosen[month]["path"]
        name = f"{to_period(month)}.pdf"
        if not source.exists():
            report.missing_file.append(to_period(month))
            continue
        wanted.add(name)
        link = links_dir / name
        link.unlink(missing_ok=True)
        # A relative target keeps the links valid if the whole repository is moved.
        link.symlink_to(os.path.relpath(source.resolve(), links_dir.resolve()))
        report.linked.append(to_period(month))
        if not has_eof_marker(source):
            report.truncated.append(to_period(month))
    for stale in links_dir.iterdir():
        if stale.is_symlink() and stale.name not in wanted:
            stale.unlink()
            report.removed.append(stale.stem)
    return report


def main() -> None:
    """Create the links and print a short report."""
    settings = Settings()
    report = link_pdfs(settings.originals_dir, settings.pdf_links_dir)
    typer.echo(f"{len(report.linked)} links in {settings.pdf_links_dir}")
    for label, periods in (
        ("truncated PDFs (no %%EOF)", report.truncated),
        ("selected but file missing", report.missing_file),
        ("stale links removed", report.removed),
    ):
        if periods:
            typer.echo(f"{label}: {', '.join(periods)}")


if __name__ == "__main__":
    typer.run(main)
