"""Ad-hoc: compare the downloaded originals with the author's edited corpus files.

Run by hand::

    uv run python adhoc/compare_with_corpus.py

For every month present in both, each downloaded version is compared line by line with the corpus file
(after decoding both and ignoring line endings). The version that differs least is reported. Writes to
``<analysis_dir>``:

* ``corpus_comparison.csv``  one row per month: best version, number of differing lines, change types
* ``corpus_diffs.csv``       one row per differing line for the best version

Differences are the author's hand edits, the encoding conversion, or things the publisher later corrected.
"""

from collections import Counter
from pathlib import Path

import typer

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index
from cof.common.settings import Settings
from cof.normalize.decode import decode_bytes
from compare_versions import Difference, diff_lines

COMPARISON_COLUMNS = ("month", "versions", "best_timestamp", "best_digest", "differing_lines", "change_types")
DIFF_COLUMNS = (
    "month",
    "digest",
    "change_type",
    "detail",
    "original_line_no",
    "corpus_line_no",
    "original",
    "corpus",
)


def compare_with_corpus(
    originals_dir: Path, corpus_dir: Path
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Compare every month that exists both as a download and in the corpus.

    Args:
        originals_dir: Directory with ``downloads.csv`` and the stored files.
        corpus_dir: Directory with the corpus files ``MMMYY.txt``.

    Returns:
        ``(comparison_rows, diff_rows)`` for the two output files.
    """
    by_month: dict[str, list[dict[str, str]]] = {}
    for row in read_rows(originals_dir / "downloads.csv"):
        if row["kind"] == "txt" and row["digest_ok"] == "1":
            by_month.setdefault(row["month"], []).append(row)
    comparison: list[dict[str, object]] = []
    diff_rows: list[dict[str, object]] = []
    for month in sorted(by_month, key=month_index):
        corpus_file = corpus_dir / f"{month}.txt"
        if not corpus_file.exists():
            continue
        corpus_lines = decode_bytes(corpus_file.read_bytes()).lines
        best: tuple[int, dict[str, str], list[Difference]] | None = None
        for version in by_month[month]:
            lines = decode_bytes((originals_dir / version["path"]).read_bytes()).lines
            diffs = diff_lines(lines, corpus_lines)  # "old" = original, "new" = corpus
            if best is None or len(diffs) < best[0]:
                best = (len(diffs), version, diffs)
        assert best is not None
        count, version, diffs = best
        types = Counter(d.change_type for d in diffs)
        comparison.append(
            {
                "month": month, "versions": len(by_month[month]), "best_timestamp": version["timestamp"],
                "best_digest": version["digest"], "differing_lines": count,
                "change_types": "; ".join(f"{k}={v}" for k, v in sorted(types.items())),
            }
        )  # fmt: skip
        for d in diffs:
            diff_rows.append(
                {
                    "month": month, "digest": version["digest"], "change_type": d.change_type,
                    "detail": d.detail, "original_line_no": d.old_line_no or "",
                    "corpus_line_no": d.new_line_no or "", "original": d.old_value, "corpus": d.new_value,
                }
            )  # fmt: skip
    return comparison, diff_rows


def main() -> None:
    """Write the comparison files and print a summary."""
    settings = Settings()
    comparison, diff_rows = compare_with_corpus(settings.originals_dir, settings.corpus_dir)
    write_rows_atomic(settings.analysis_dir / "corpus_comparison.csv", COMPARISON_COLUMNS, comparison)
    write_rows_atomic(settings.analysis_dir / "corpus_diffs.csv", DIFF_COLUMNS, diff_rows)
    identical = [r for r in comparison if r["differing_lines"] == 0]
    typer.echo(f"{len(comparison)} months in both; {len(identical)} identical after decoding")
    for r in comparison:
        if r["differing_lines"]:
            typer.echo(f"  {r['month']}: {r['differing_lines']} lines  {r['change_types']}")


if __name__ == "__main__":
    typer.run(main)
