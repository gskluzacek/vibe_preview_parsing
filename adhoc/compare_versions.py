"""Ad-hoc: classify the differences between the published versions of each multi-version month.

Run by hand::

    uv run python adhoc/compare_versions.py

Reads ``<originals>/downloads.csv`` and the stored text files, compares each month's versions in capture
order (oldest first, each against the next), and writes ``<originals>/version_diffs.csv`` with one row
per differing line. The labels show what kinds of defects the publisher later corrected, which feeds the
rule discovery and the choice of the best version.
"""

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

import typer

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index
from cof.common.settings import Settings
from cof.normalize.decode import decode_bytes

COLUMNS = (
    "month", "old_digest", "new_digest", "old_capture", "new_capture", "change_type", "detail",
    "old_line_no", "new_line_no", "old_value", "new_value",
)  # fmt: skip
# Item fields of the canonical layout (spec section 4.1).
FIELD_NAMES = ("flag", "sol_code", "sol_text", "date", "price", "tail", "extra")
_TAB_RUN = re.compile(r"\t+")


@dataclass(frozen=True)
class Difference:
    """One differing line between two versions."""

    change_type: str
    detail: str
    old_line_no: int | None
    new_line_no: int | None
    old_value: str
    new_value: str


def classify_pair(old: str, new: str) -> tuple[str, str]:
    """Label how one line changed into another.

    Args:
        old: The line in the older version.
        new: The line in the newer version.

    Returns:
        ``(change_type, detail)``. Types: ``ident_line``, ``whitespace``, ``tab_count``, ``item_<field>``,
        ``text_line``.
    """
    if old.strip() == new.strip():
        return "whitespace", "leading/trailing whitespace changed"
    if old.startswith("PREVIEWS ") and new.startswith("PREVIEWS "):
        return "ident_line", f"identification line corrected from: {old} to {new}"
    old_fields, new_fields = old.split("\t"), new.split("\t")
    if len(old_fields) >= 5 and len(new_fields) >= 5:
        if len(old_fields) != len(new_fields) or [len(r) for r in _TAB_RUN.findall(old)] != [
            len(r) for r in _TAB_RUN.findall(new)
        ]:
            old_runs, new_runs = _TAB_RUN.findall(old), _TAB_RUN.findall(new)
            where = next((i for i, (a, b) in enumerate(zip(old_runs, new_runs, strict=False)) if a != b), 0)
            first = FIELD_NAMES[min(where, len(FIELD_NAMES) - 1)]
            second = FIELD_NAMES[min(where + 1, len(FIELD_NAMES) - 1)]
            return "tab_count", f"corrected number of tabs between {first} and {second}"
        changed = [
            FIELD_NAMES[min(i, len(FIELD_NAMES) - 1)]
            for i, (a, b) in enumerate(zip(old_fields, new_fields, strict=True))
            if a != b
        ]
        return "item_" + "+".join(changed), "changed field(s): " + ", ".join(changed)
    return "text_line", "non-item line changed"


def diff_lines(old: list[str], new: list[str]) -> list[Difference]:
    """Compare two versions line by line.

    Args:
        old: Lines of the older version.
        new: Lines of the newer version.

    Returns:
        One :class:`Difference` per changed, added or removed line.
    """
    out: list[Difference] = []
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        paired = min(i2 - i1, j2 - j1) if tag == "replace" else 0
        for k in range(paired):  # lines replaced one for one
            kind, detail = classify_pair(old[i1 + k], new[j1 + k])
            out.append(Difference(kind, detail, i1 + k + 1, j1 + k + 1, old[i1 + k], new[j1 + k]))
        for k in range(i1 + paired, i2):
            out.append(Difference("line_removed", "line only in older version", k + 1, None, old[k], ""))
        for k in range(j1 + paired, j2):
            out.append(Difference("line_added", "line only in newer version", None, k + 1, "", new[k]))
    return out


def compare_versions(originals_dir: Path) -> list[dict[str, object]]:
    """Compare every multi-version text month.

    Args:
        originals_dir: Directory with ``downloads.csv`` and the stored files.

    Returns:
        Rows for ``version_diffs.csv``.
    """
    by_month: dict[str, list[dict[str, str]]] = {}
    for row in read_rows(originals_dir / "downloads.csv"):
        if row["kind"] == "txt" and row["digest_ok"] == "1":
            by_month.setdefault(row["month"], []).append(row)
    rows: list[dict[str, object]] = []
    for month in sorted(by_month, key=month_index):
        versions = sorted(by_month[month], key=lambda r: r["timestamp"])
        for older, newer in zip(versions, versions[1:], strict=False):
            a = decode_bytes((originals_dir / older["path"]).read_bytes())
            b = decode_bytes((originals_dir / newer["path"]).read_bytes())
            diffs = diff_lines(a.lines, b.lines)
            if not diffs and a.encoding == b.encoding:  # the digests differ but the content does not
                how = f"identical content; older stored as {a.compression}, newer as {b.compression}"
                diffs = [Difference("no_content_difference", how, None, None, "", "")]
            if a.encoding != b.encoding:  # worth noting when the publisher changed the encoding
                diffs.insert(0, Difference("encoding", f"{a.encoding} -> {b.encoding}", None, None, "", ""))
            for d in diffs:
                rows.append(
                    {
                        "month": month, "old_digest": older["digest"], "new_digest": newer["digest"],
                        "old_capture": older["timestamp"], "new_capture": newer["timestamp"],
                        "change_type": d.change_type, "detail": d.detail,
                        "old_line_no": d.old_line_no or "", "new_line_no": d.new_line_no or "",
                        "old_value": d.old_value, "new_value": d.new_value,
                    }
                )  # fmt: skip
    return rows


def main() -> None:
    """Write ``version_diffs.csv`` and print a summary of the change types."""
    originals = Settings().originals_dir
    rows = compare_versions(originals)
    write_rows_atomic(originals / "version_diffs.csv", COLUMNS, rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[str(r["change_type"])] = counts.get(str(r["change_type"]), 0) + 1
    typer.echo(f"{len(rows)} differing lines in {len({r['month'] for r in rows})} month(s)")
    for kind, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        typer.echo(f"  {n:6d}  {kind}")


if __name__ == "__main__":
    typer.run(main)
