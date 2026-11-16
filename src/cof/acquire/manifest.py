"""Stage 1c: turn the raw index answers into the manifest, and summarize coverage."""

import json
from collections import defaultdict
from pathlib import Path

from cof.acquire.index import raw_cdx_dir
from cof.acquire.models import MANIFEST_COLUMNS, Capture
from cof.acquire.params import AcquireParams
from cof.acquire.urls import classify
from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index, months_between

_TABLE_HEADER = "Per month (captures / distinct files / eras), blank = none"


def build_captures(params: AcquireParams, acquire_dir: Path) -> tuple[list[Capture], int]:
    """Read the raw index files and classify every row.

    Args:
        params: Configuration (pattern names and plausibility thresholds).
        acquire_dir: Directory holding ``raw/cdx/*.json``.

    Returns:
        ``(captures, skipped)``: one capture per index row that is a single COF file, sorted by month,
        kind and time, and the number of rows that were not (folders, error addresses, other pages).
    """
    captures: list[Capture] = []
    skipped = 0
    for name in params.patterns:
        path = raw_cdx_dir(acquire_dir) / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        ix = {field: i for i, field in enumerate(data["header"])}
        for row in data["rows"]:
            cof = classify(row[ix["original"]])
            if cof is None:
                skipped += 1
                continue
            rule = params.plausible[cof.kind]
            raw_length = row[ix["length"]]
            length = int(raw_length) if raw_length.isdigit() else 0
            ok = (
                row[ix["statuscode"]] == "200"
                and row[ix["mimetype"]] == rule.mime
                and length >= rule.min_length
            )
            captures.append(
                Capture(
                    month=cof.month,
                    kind=cof.kind,
                    era=cof.era,
                    timestamp=row[ix["timestamp"]],
                    original=row[ix["original"]],
                    status=row[ix["statuscode"]],
                    mime=row[ix["mimetype"]],
                    length=length,
                    digest=row[ix["digest"]],
                    plausible=ok,
                )
            )
    captures.sort(key=lambda c: (month_index(c.month), c.kind, c.timestamp, c.original))
    return captures, skipped


def write_manifest(params: AcquireParams, acquire_dir: Path) -> tuple[int, int, int]:
    """Build ``manifest.csv`` from the raw index files.

    Args:
        params: Configuration.
        acquire_dir: Directory holding the raw index; the manifest is written here.

    Returns:
        ``(captures, plausible, skipped)`` counts.
    """
    captures, skipped = build_captures(params, acquire_dir)
    write_rows_atomic(acquire_dir / "manifest.csv", MANIFEST_COLUMNS, (c.to_row() for c in captures))
    return len(captures), sum(c.plausible for c in captures), skipped


def read_manifest(acquire_dir: Path) -> list[Capture]:
    """Read ``manifest.csv``.

    Args:
        acquire_dir: Directory holding the manifest.

    Returns:
        All captures, in file order.

    Raises:
        FileNotFoundError: If there is no manifest yet.
    """
    path = acquire_dir / "manifest.csv"
    if not path.exists():
        raise FileNotFoundError(f"no manifest at {path}; build it first")
    return [Capture.from_row(row) for row in read_rows(path)]


def coverage_report(params: AcquireParams, acquire_dir: Path) -> tuple[str, str]:
    """Summarize which months have a plausible capture.

    Args:
        params: Configuration (expected month range).
        acquire_dir: Directory with ``manifest.csv`` and, optionally, ``listing_links.csv``.

    Returns:
        ``(full_text, summary_text)``; the summary is the part before the per-month table.
    """
    by: dict[tuple[str, str], list[Capture]] = defaultdict(list)
    for cap in read_manifest(acquire_dir):
        if cap.plausible:
            by[(cap.month, cap.kind)].append(cap)
    listed: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in read_rows(acquire_dir / "listing_links.csv"):
        listed[(row["month"], row["kind"])].add(row["capture"][:4])

    months = months_between(params.expect_from, params.expect_to)
    lines = [
        f"COF coverage {params.expect_from}-{params.expect_to} "
        "(plausible = status 200, expected MIME type and size)",
        "",
    ]
    for kind in ("txt", "pdf"):
        missing = [m for m in months if not by[(m, kind)]]
        multi = [m for m in months if len({c.digest for c in by[(m, kind)]}) > 1]
        eras: dict[str, int] = defaultdict(int)
        for m in months:
            for era in {c.era for c in by[(m, kind)]}:
                eras[f"era{era}"] += 1
        lines += [
            f"{kind.upper()}: {len(months) - len(missing)} of {len(months)} months have a plausible capture",
            f"  months seen per URL era: {dict(sorted(eras.items()))}",
            f"  missing: {' '.join(missing) or 'none'}",
            f"  months with more than one distinct file (compare these): {len(multi)}",
            f"    {' '.join(multi) or 'none'}",
            "",
        ]
    summary = "\n".join(lines)
    lines += [_TABLE_HEADER, "month   txt          pdf          listed-on-page-years"]
    for m in months:
        cells: list[str] = []
        for kind in ("txt", "pdf"):
            caps = by[(m, kind)]
            if caps:
                eras_seen = "".join(sorted({str(c.era) for c in caps}))
                cells.append(f"{len(caps)}/{len({c.digest for c in caps})}/{eras_seen}")
            else:
                cells.append("")
        years = ",".join(sorted(listed[(m, "txt")] | listed[(m, "pdf")]))
        lines.append(f"{m:<7} {cells[0]:<12} {cells[1]:<12} {years}")
    return "\n".join(lines) + "\n", summary
