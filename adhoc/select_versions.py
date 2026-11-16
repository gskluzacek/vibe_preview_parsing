"""Ad-hoc: choose the best downloaded version of each month and record why the others were not used.

Run by hand::

    uv run python adhoc/select_versions.py

Writes ``<originals>/selection.csv`` with one row per downloaded file (text and PDF):

    month, kind, digest, timestamp, path, status, reason_code, reason_detail

``status`` is ``selected``, ``only_version`` or ``not_used``. The rules (text):

1. Copies with identical decoded content are collapsed; a plain copy is preferred to a gzip one, then the
   earliest capture. The others are ``not_used`` with reason ``identical_content``.
2. Among different contents, the best has: no foreign layout / truncation / empty file; then fewest
   errors; then fewest open warnings; then the most non-blank lines (completeness); then the fewest
   automatically fixable issues; then the latest capture.
3. For PDFs, a truncated file (no ``%%EOF``) is never selected; among complete ones the latest is used.

Manual overrides: ``config/selection_overrides.yaml``.
"""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import typer

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index
from cof.common.settings import Settings, load_yaml
from cof.normalize.context import Issue, build_context
from cof.normalize.decode import Decoded
from cof.normalize.rules import Rule, detect_all, load_rules
from compare_versions import Difference, diff_lines

COLUMNS = ("month", "kind", "digest", "timestamp", "path", "status", "reason_code", "reason_detail")
_BLOCKING = {"F01", "F05", "F10"}  # the file cannot be a good version of its month


@dataclass(frozen=True)
class Candidate:
    """One downloaded text file with the facts used to rank it."""

    row: dict[str, str]
    decoded: Decoded
    issues: list[Issue]
    rules: dict[str, Rule]

    @property
    def timestamp(self) -> str:
        """Capture time."""
        return self.row["timestamp"]

    @property
    def blocking(self) -> int:
        """1 if the file is a foreign layout, truncated or empty, else 0."""
        return int(any(i.rule_id in _BLOCKING for i in self.issues))

    def count(self, severity: str | None = None, rule_class: str | None = None) -> int:
        """Count issues, optionally limited to a severity and/or rule class."""
        return sum(
            1
            for i in self.issues
            if (severity is None or self.rules[i.rule_id].severity == severity)
            and (rule_class is None or self.rules[i.rule_id].rule_class == rule_class)
        )

    @property
    def nonblank_lines(self) -> int:
        """Number of lines with content (a measure of completeness)."""
        return sum(1 for line in self.decoded.lines if line.strip())

    def rank(self) -> tuple[int, int, int, int, int]:
        """Sort key: smaller is better (the capture time is applied separately, latest first)."""
        open_warnings = sum(
            1
            for i in self.issues
            if self.rules[i.rule_id].rule_class == "open" and self.rules[i.rule_id].severity == "warning"
        )
        fixable = self.count(rule_class="auto-lossless") + self.count(rule_class="auto-derived")
        return (self.blocking, self.count(severity="error"), open_warnings, -self.nonblank_lines, fixable)


def describe_difference(unused: Candidate, selected: Candidate) -> tuple[str, str]:
    """Explain in words how an unused version differs from the selected one.

    Args:
        unused: The version that was not chosen.
        selected: The chosen version of the same month.

    Returns:
        ``(reason_code, reason_detail)``.
    """
    later = selected.timestamp > unused.timestamp
    diffs: list[Difference] = diff_lines(unused.decoded.lines, selected.decoded.lines)
    # Blocking problems come first: they make the version unusable whatever else differs.
    for code, text in (
        ("F01", "foreign layout: not a COF text file"),
        ("F05", "gzip stream truncated"),
        ("F10", "empty file"),
    ):
        if any(i.rule_id == code for i in unused.issues):
            return {"F01": "foreign_layout", "F05": "truncated", "F10": "empty"}[code], text
    parts: list[str] = []
    for d in diffs:
        if d.change_type == "ident_line":
            old, new = d.old_value, d.new_value
            parts.append(
                f"identification line corrected from: {old} to {new}"
                if later
                else f"identification line differs: {old} (this version) vs {new} (selected)"
            )
        elif d.change_type == "tab_count":
            parts.append(d.detail)
        elif d.change_type == "line_added":
            parts.append(f"selected version has an extra line: {d.new_value.strip()[:60]!r}")
        elif d.change_type == "line_removed":
            parts.append(f"this version has an extra line: {d.old_value.strip()[:60]!r}")
        elif d.change_type == "whitespace":
            parts.append("whitespace differs")
        else:
            parts.append(f"{d.change_type}: {d.detail}")
    unique = list(dict.fromkeys(parts))
    shown = "; ".join(unique[:3]) + (
        f"; and {len(unique) - 3} more kind(s) of difference" if len(unique) > 3 else ""
    )
    if not diffs:
        return "identical_content", "identical content to the selected version"
    code = (
        "fewer_defects"
        if unused.rank() > selected.rank()
        else "later_version"
        if later
        else "earlier_version"
    )
    return code, shown


def choose_text(candidates: list[Candidate]) -> tuple[Candidate, dict[str, tuple[str, str]]]:
    """Choose the best text version of one month.

    Args:
        candidates: All downloaded text versions of the month.

    Returns:
        ``(selected, reasons)`` where ``reasons`` maps each other candidate's digest to
        ``(reason_code, reason_detail)``.
    """
    # Collapse copies whose decoded content is identical: keep a plain copy, then the earliest.
    groups: dict[str, list[Candidate]] = defaultdict(list)
    for cand in candidates:
        groups[cand.decoded.text].append(cand)
    representatives: list[Candidate] = []
    reasons: dict[str, tuple[str, str]] = {}
    for members in groups.values():
        members.sort(key=lambda c: (c.decoded.compression != "none", c.timestamp))
        representatives.append(members[0])
        for other in members[1:]:
            reasons[other.row["digest"]] = (
                "identical_content",
                f"identical content to {members[0].row['timestamp'][:8]} capture (this copy stored as "
                f"{other.decoded.compression}, kept copy as {members[0].decoded.compression})",
            )
    representatives.sort(key=lambda c: c.timestamp, reverse=True)  # latest first, then a stable sort on rank
    selected = min(representatives, key=lambda c: c.rank())
    for cand in representatives:
        if cand is not selected:
            code, detail = describe_difference(cand, selected)
            reasons[cand.row["digest"]] = (
                code,
                f"{detail} (this capture {cand.timestamp[:8]}, selected {selected.timestamp[:8]})",
            )
    return selected, reasons


def select_all(originals_dir: Path, settings: Settings) -> list[dict[str, object]]:
    """Build the selection rows for every downloaded file.

    Args:
        originals_dir: Directory with ``downloads.csv`` and the stored files.
        settings: Settings (for the rules and the override file).

    Returns:
        Rows for ``selection.csv``, ordered by month, kind and capture time.
    """
    rules = load_rules(settings)
    overrides = {
        (o["month"], o["kind"]): o
        for o in load_yaml("selection_overrides.yaml", settings).get("overrides") or []
    }
    by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_rows(originals_dir / "downloads.csv"):
        if row["digest_ok"] == "1":
            by_key[(row["month"], row["kind"])].append(row)
    out: list[dict[str, object]] = []
    for (month, kind), rows in sorted(by_key.items(), key=lambda kv: (month_index(kv[0][0]), kv[0][1])):
        decisions: dict[str, tuple[str, str, str]] = {}  # digest -> (status, code, detail)
        if kind == "txt":
            cands = []
            for row in rows:
                ctx = build_context(month, (originals_dir / row["path"]).read_bytes())
                cands.append(Candidate(row, ctx.decoded, detect_all(ctx), rules))
            selected, reasons = choose_text(cands)
            chosen = selected.row["digest"]
            if (month, kind) in overrides:
                chosen = overrides[(month, kind)]["digest"]
            only = len(rows) == 1
            for cand in cands:
                digest = cand.row["digest"]
                if digest == chosen:
                    note = overrides.get((month, kind), {}).get("reason", "")
                    decisions[digest] = ("only_version" if only else "selected", "", note)
                else:
                    code, detail = reasons.get(digest, ("not_chosen", "overridden by hand"))
                    decisions[digest] = ("not_used", code, detail)
        else:
            complete = [r for r in rows if r["content_ok"] == "1"]
            chosen = max(complete, key=lambda r: r["timestamp"])["digest"] if complete else ""
            if (month, kind) in overrides:
                chosen = overrides[(month, kind)]["digest"]
            for row in rows:
                digest = row["digest"]
                if row["content_ok"] != "1":
                    decisions[digest] = ("not_used", "truncated", "PDF file was truncated (no %%EOF marker)")
                elif digest == chosen:
                    decisions[digest] = ("only_version" if len(rows) == 1 else "selected", "", "")
                else:
                    decisions[digest] = (
                        "not_used",
                        "superseded",
                        "a later complete PDF capture was selected (content not compared)",
                    )
        for row in sorted(rows, key=lambda r: r["timestamp"]):
            status, code, detail = decisions[row["digest"]]
            out.append(
                {
                    "month": month, "kind": kind, "digest": row["digest"], "timestamp": row["timestamp"],
                    "path": row["path"], "status": status, "reason_code": code, "reason_detail": detail,
                }
            )  # fmt: skip
    return out


def main() -> None:
    """Write ``selection.csv`` and print a summary."""
    settings = Settings()
    rows = select_all(settings.originals_dir, settings)
    write_rows_atomic(settings.originals_dir / "selection.csv", COLUMNS, rows)
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for r in rows:
        counts[(str(r["kind"]), str(r["status"]), str(r["reason_code"]))] += 1
    for key, n in sorted(counts.items()):
        typer.echo(f"{n:5d}  {key[0]}  {key[1]:<13} {key[2]}")
    months_txt = {str(r["month"]) for r in rows if r["kind"] == "txt"}
    chosen_txt = {
        str(r["month"]) for r in rows if r["kind"] == "txt" and r["status"] in ("selected", "only_version")
    }
    typer.echo(f"text months: {len(months_txt)}, with a selected version: {len(chosen_txt)}")


if __name__ == "__main__":
    typer.run(main)
