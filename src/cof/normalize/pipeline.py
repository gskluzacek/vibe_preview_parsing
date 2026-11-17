"""Run the normalizer over every selected text file and write the clean files and the reports."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index, to_period
from cof.common.settings import Settings, load_yaml
from cof.normalize.normalize import NormalizedFile, Patch, normalize_file
from cof.normalize.rules import load_rules

ISSUE_COLUMNS = (
    "month",
    "period",
    "rule_id",
    "line",
    "class",
    "status",
    "before",
    "after",
    "how",
    "evidence",
)
SUMMARY_COLUMNS = (
    "month", "period", "digest", "timestamp", "status", "source_encoding", "compression", "source_eol",
    "source_lines", "output_rows", "sidecar_rows", "dropped_lines", "non_ascii_bytes",
    "fixed", "patched", "open", "info",
)  # fmt: skip
LEDGER_COLUMNS = ("month", "period", "line_type", "fate", "lines")
IDENT_COLUMNS = (
    "month", "period", "source_encoding", "ident_present", "ident_lines", "ident_variant",
    "ident_month", "ident_year", "ident_volume", "ident_issue", "ident_catalog",
    "expected_year", "expected_month", "expected_volume", "expected_issue", "expected_catalog",
    "item_catalog", "month_ok", "year_ok", "issue_ok", "catalog_ident_ok", "catalog_item_ok",
)  # fmt: skip
_OUTPUT_NAME = re.compile(r"^\d{4}_\d\d\.txt$")


@dataclass
class RunResult:
    """What a pipeline run produced."""

    files: int = 0
    rejected: int = 0
    fixed: int = 0
    open: int = 0
    removed: int = 0  # stale output files deleted


def load_patches(settings: Settings) -> list[Patch]:
    """Read ``config/patches.yaml``.

    Args:
        settings: Settings giving the configuration directory.

    Returns:
        The reviewed patches (empty if none).
    """
    return [Patch.model_validate(p) for p in load_yaml("patches.yaml", settings).get("patches") or []]


def run_pipeline(
    settings: Settings,
    months: set[str] | None = None,
    say: Callable[[str], None] = print,
    full_checks: bool = False,
) -> RunResult:
    """Normalize every selected text file.

    Reads ``<originals>/selection.csv``. Writes ``<normalized>/YYYY_MM.txt`` for each file and, when a file
    has lines that are neither headings nor items, ``<normalized>/sidecar/YYYY_MM.txt``. A full run
    (``months`` is ``None``) also writes ``issues.csv``, ``summary.csv``, ``ledger.csv`` (every source line
    counted by type and fate) and ``idents.csv`` (identification facts), and removes output files that no
    longer correspond to a selected month.

    Args:
        settings: Project settings (directories and configuration).
        months: Restrict the run to these month codes; ``None`` means all.
        say: Called with one line of progress text.
        full_checks: Also run the rules marked ``optional`` in ``config/rules.yaml``.

    Returns:
        Counts of files, rejections and issues.
    """
    rules = load_rules(settings)
    patches = load_patches(settings)
    selection = [
        r
        for r in read_rows(settings.originals_dir / "selection.csv")
        if r["kind"] == "txt" and r["status"] in ("selected", "only_version")
    ]
    selection.sort(key=lambda r: month_index(r["month"]))
    out_dir = settings.normalized_dir
    side_dir = out_dir / "sidecar"
    out_dir.mkdir(parents=True, exist_ok=True)
    side_dir.mkdir(exist_ok=True)
    result = RunResult()
    issue_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    ledger_rows: list[dict[str, object]] = []
    ident_rows: list[dict[str, object]] = []
    written: set[str] = set()
    for row in selection:
        if months is not None and row["month"] not in months:
            continue
        done: NormalizedFile = normalize_file(
            row["month"], (settings.originals_dir / row["path"]).read_bytes(), rules, patches, full_checks
        )
        result.files += 1
        if done.text is None:
            result.rejected += 1
            say(f"REJECTED {done.month}: not a COF text file")
        else:
            (out_dir / f"{done.period}.txt").write_bytes(done.text.encode("utf-8"))
            written.add(f"{done.period}.txt")
            side_path = side_dir / f"{done.period}.txt"
            if done.sidecar is not None:
                side_path.write_bytes(done.sidecar.encode("utf-8"))
            else:
                side_path.unlink(missing_ok=True)
            for (line_type, fate), count in sorted(done.ledger.items()):
                ledger_rows.append(
                    {
                        "month": done.month,
                        "period": done.period,
                        "line_type": line_type,
                        "fate": fate,
                        "lines": count,
                    }
                )
            ident_rows.append(
                {"month": done.month, "period": done.period, "source_encoding": done.encoding, **done.ident}
            )
        result.fixed += done.count("fixed")
        result.open += done.count("open")
        for rec in done.records:
            issue_rows.append(
                {
                    "month": done.month, "period": done.period, "rule_id": rec.rule_id,
                    "line": rec.line or "",
                    "class": rec.rule_class, "status": rec.status, "before": rec.before, "after": rec.after,
                    "how": rec.how, "evidence": rec.evidence,
                }
            )  # fmt: skip
        summary_rows.append(
            {
                "month": done.month, "period": done.period, "digest": row["digest"],
                "timestamp": row["timestamp"],
                "status": done.status, "source_encoding": done.encoding, "compression": done.compression,
                "source_eol": done.eol, "source_lines": done.source_lines, "output_rows": done.output_rows,
                "sidecar_rows": done.sidecar_rows,
                "dropped_lines": sum(n for (_, fate), n in done.ledger.items() if fate == "dropped"),
                "non_ascii_bytes": done.non_ascii_bytes, "fixed": done.count("fixed"),
                "patched": done.count("patched"), "open": done.count("open"), "info": done.count("info"),
            }
        )  # fmt: skip
    if months is None:
        for path in out_dir.iterdir():
            if _OUTPUT_NAME.match(path.name) and path.name not in written:
                path.unlink()
                (side_dir / path.name).unlink(missing_ok=True)
                result.removed += 1
        write_rows_atomic(out_dir / "issues.csv", ISSUE_COLUMNS, issue_rows)
        write_rows_atomic(out_dir / "summary.csv", SUMMARY_COLUMNS, summary_rows)
        write_rows_atomic(out_dir / "ledger.csv", LEDGER_COLUMNS, ledger_rows)
        write_rows_atomic(out_dir / "idents.csv", IDENT_COLUMNS, ident_rows)
    say(f"{result.files} files, {result.rejected} rejected, {result.fixed} issues fixed, {result.open} open")
    return result


def period_of(month: str) -> str:
    """Return the output period name for a month code (kept here for callers of the pipeline)."""
    return to_period(month)
