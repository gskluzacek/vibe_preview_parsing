"""Stage 1d: download COF files from the archive, one per distinct content version, and verify them.

Files are stored exactly as fetched and never edited::

    <originals>/<kind>/<MMMYY>/<digest>_<timestamp>.<ext>
    <originals>/downloads.csv        one row per file: where it came from, sizes, checks

Each file is checked against the archive's digest (base32 SHA-1 of the bytes) and for completeness.
A file that fails a check is kept and flagged in the log, never silently dropped.
"""

import base64
import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from cof.acquire.models import Capture
from cof.acquire.wayback import WaybackClient, WaybackError
from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index

LOG_COLUMNS: tuple[str, ...] = (
    "month", "kind", "era", "digest", "timestamp", "original", "path", "bytes", "sha256",
    "digest_ok", "content_ok", "fetched_utc",
)  # fmt: skip


def archive_digest(data: bytes) -> str:
    """Compute the archive's content digest.

    Args:
        data: File bytes.

    Returns:
        Base32 text of the SHA-1 of ``data``, the form the index uses.
    """
    return base64.b32encode(hashlib.sha1(data).digest()).decode()


def looks_right(kind: str, data: bytes) -> bool:
    """Run a cheap sanity check on downloaded content.

    A valid digest only proves the bytes match what the archive stored; the archive can have stored a
    truncated file. A PDF must therefore start with ``%PDF`` and end with ``%%EOF``. Text must not be an
    HTML page.

    Args:
        kind: ``"txt"`` or ``"pdf"``.
        data: File bytes.

    Returns:
        True if the content looks like a complete file of that kind.
    """
    if kind == "pdf":
        return data[:5] == b"%PDF-" and b"%%EOF" in data[-1024:]
    head = data[:2000].lstrip().lower()
    return not head.startswith((b"<!doctype", b"<html"))


def distinct_versions(captures: Iterable[Capture], months: set[str], kinds: set[str]) -> list[Capture]:
    """Pick the earliest plausible capture of each distinct content version.

    Args:
        captures: Manifest captures.
        months: Month codes to include.
        kinds: ``"txt"`` and/or ``"pdf"``.

    Returns:
        One capture per ``(month, kind, digest)``, in the order first seen.
    """
    chosen: dict[tuple[str, str, str], Capture] = {}
    for cap in captures:
        if not cap.plausible or cap.month not in months or cap.kind not in kinds:
            continue
        key = (cap.month, cap.kind, cap.digest)
        if key not in chosen or cap.timestamp < chosen[key].timestamp:
            chosen[key] = cap
    return list(chosen.values())


def stored_path(originals_dir: Path, cap: Capture) -> Path:
    """Return where a capture is stored on disk."""
    return originals_dir / cap.kind / cap.month / f"{cap.digest}_{cap.timestamp}.{cap.kind}"


@dataclass
class FetchSummary:
    """What a fetch run did."""

    considered: int = 0
    fetched: int = 0
    skipped: int = 0
    failed: list[str] = field(default_factory=list)  # relative paths that could not be fetched


def run_fetch(
    client: WaybackClient | None,
    captures: list[Capture],
    originals_dir: Path,
    wanted: Iterable[tuple[str, str]],
    say: Callable[[str], None],
    dry_run: bool = False,
) -> FetchSummary:
    """Download every distinct version of the wanted months and verify it.

    Existing verified files are skipped, so a run can be repeated safely. A failed download does not
    stop the run; it is listed in the summary and retried next time.

    Args:
        client: Archive client; may be ``None`` for a dry run.
        captures: Manifest captures.
        originals_dir: Root directory for downloaded files and ``downloads.csv``.
        wanted: ``(month, kind)`` pairs to fetch.
        say: Called with one line of progress text per file.
        dry_run: Only report what would be fetched.

    Returns:
        Counts and the list of failures.
    """
    log_path = originals_dir / "downloads.csv"
    log = read_rows(log_path)
    done = {row["path"] for row in log if row["digest_ok"] == "1"}
    for row in log:  # re-check files already on disk with the current checks
        existing = originals_dir / row["path"]
        if existing.exists():
            row["content_ok"] = str(int(looks_right(row["kind"], existing.read_bytes())))

    todo: list[Capture] = []
    for month, kind in wanted:
        todo += distinct_versions(captures, {month}, {kind})
    summary = FetchSummary(considered=len(todo))

    for cap in todo:
        target = stored_path(originals_dir, cap)
        rel = target.relative_to(originals_dir).as_posix()
        if rel in done and target.exists():
            row = next(r for r in log if r["path"] == rel)
            say(f"have    {rel}" + ("" if row["content_ok"] == "1" else " CONTENT CHECK FAILED"))
            summary.skipped += 1
            continue
        if dry_run or client is None:
            say(f"would   {rel} {cap.original}")
            continue
        try:
            data = client.fetch_capture(cap.timestamp, cap.original)
        except WaybackError as error:
            summary.failed.append(rel)
            say(f"FAILED  {rel} {error}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digest_ok = archive_digest(data) == cap.digest
        log = [row for row in log if row["path"] != rel]
        log.append(
            {
                "month": cap.month, "kind": cap.kind, "era": str(cap.era), "digest": cap.digest,
                "timestamp": cap.timestamp, "original": cap.original, "path": rel, "bytes": str(len(data)),
                "sha256": hashlib.sha256(data).hexdigest(), "digest_ok": str(int(digest_ok)),
                "content_ok": str(int(looks_right(cap.kind, data))),
                "fetched_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )  # fmt: skip
        summary.fetched += 1
        say(f"{'fetched ' if digest_ok else 'DIGEST MISMATCH '}{rel} {len(data)} bytes")
        _write_log(log_path, log)  # after every file, so an interrupted run keeps its progress
    if log and not dry_run:
        _write_log(log_path, log)
    return summary


def _write_log(path: Path, log: list[dict[str, str]]) -> None:
    """Write the download log sorted by month, kind and capture time."""
    ordered = sorted(log, key=lambda r: (month_index(r["month"]), r["kind"], r["timestamp"]))
    write_rows_atomic(path, LOG_COLUMNS, ordered)
