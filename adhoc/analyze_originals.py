"""Ad-hoc: run every detector over every downloaded text file and summarize what is wrong.

Run by hand::

    uv run python adhoc/analyze_originals.py

Writes three files to ``<analysis_dir>`` (default ``data/original_analysis``):

* ``issues.csv``      one row per issue: file, month, rule, line, evidence
* ``files.csv``       one row per file: encoding facts, line counts, issue counts by severity
* ``rules.csv``       one row per rule: how many files and issues, and in which months it occurs

This is detect-only: nothing is fixed. The same detectors later drive the normalizer.
"""

from collections import Counter, defaultdict
from pathlib import Path

import typer

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.months import month_index
from cof.common.settings import Settings
from cof.normalize.classify import LineType
from cof.normalize.context import build_context
from cof.normalize.rules import detect_all, load_rules

ISSUE_COLUMNS = ("path", "month", "timestamp", "rule_id", "line", "evidence")
FILE_COLUMNS = (
    "path", "month", "timestamp", "digest", "encoding", "eol", "compression", "lines", "items", "pages",
    "headings", "errors", "warnings", "infos",
)  # fmt: skip
RULE_COLUMNS = ("rule_id", "name", "class", "severity", "anomaly", "files", "issues", "months")


def analyze(
    originals_dir: Path, settings: Settings
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Run all detectors over all downloaded text files.

    Args:
        originals_dir: Directory with ``downloads.csv`` and the stored files.
        settings: Settings (used to locate ``config/rules.yaml``).

    Returns:
        ``(issue_rows, file_rows, rule_rows)`` ready to be written as CSV.
    """
    rules = load_rules(settings)
    entries = [
        r for r in read_rows(originals_dir / "downloads.csv") if r["kind"] == "txt" and r["digest_ok"] == "1"
    ]
    entries.sort(key=lambda r: (month_index(r["month"]), r["timestamp"]))
    issue_rows: list[dict[str, object]] = []
    file_rows: list[dict[str, object]] = []
    files_by_rule: dict[str, set[str]] = defaultdict(set)
    count_by_rule: Counter[str] = Counter()
    months_by_rule: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        ctx = build_context(entry["month"], (originals_dir / entry["path"]).read_bytes())
        issues = detect_all(ctx)
        severity = Counter(rules[i.rule_id].severity for i in issues)
        kinds = Counter(ctx.types)
        file_rows.append(
            {
                "path": entry["path"], "month": entry["month"], "timestamp": entry["timestamp"],
                "digest": entry["digest"], "encoding": ctx.decoded.encoding, "eol": ctx.decoded.eol,
                "compression": ctx.decoded.compression, "lines": len(ctx.lines),
                "items": kinds[LineType.ITEM], "pages": kinds[LineType.PAGE],
                "headings": kinds[LineType.HEADING], "errors": severity["error"],
                "warnings": severity["warning"], "infos": severity["info"],
            }
        )  # fmt: skip
        for issue in issues:
            issue_rows.append(
                {
                    "path": entry["path"], "month": entry["month"], "timestamp": entry["timestamp"],
                    "rule_id": issue.rule_id, "line": issue.line or "", "evidence": issue.evidence,
                }
            )  # fmt: skip
            files_by_rule[issue.rule_id].add(entry["path"])
            count_by_rule[issue.rule_id] += 1
            months_by_rule[issue.rule_id].add(entry["month"])
    rule_rows: list[dict[str, object]] = []
    for rule_id, rule in rules.items():
        months = sorted(months_by_rule[rule_id], key=month_index)
        rule_rows.append(
            {
                "rule_id": rule_id, "name": rule.name, "class": rule.rule_class, "severity": rule.severity,
                "anomaly": rule.anomaly or "", "files": len(files_by_rule[rule_id]),
                "issues": count_by_rule[rule_id],
                "months": " ".join(months[:12]) + (f" ... (+{len(months) - 12})" if len(months) > 12 else ""),
            }
        )  # fmt: skip
    return issue_rows, file_rows, rule_rows


def main() -> None:
    """Analyze all files, write the CSV outputs, and print the per-rule summary."""
    settings = Settings()
    issue_rows, file_rows, rule_rows = analyze(settings.originals_dir, settings)
    out = settings.analysis_dir
    write_rows_atomic(out / "issues.csv", ISSUE_COLUMNS, issue_rows)
    write_rows_atomic(out / "files.csv", FILE_COLUMNS, file_rows)
    write_rows_atomic(out / "rules.csv", RULE_COLUMNS, rule_rows)
    typer.echo(f"{len(file_rows)} files, {len(issue_rows)} issues")
    typer.echo(f"{'rule':<5}{'name':<30}{'class':<14}{'files':>6}{'issues':>9}")
    for row in rule_rows:
        typer.echo(
            f"{row['rule_id']!s:<5}{row['name']!s:<30}{row['class']!s:<14}{row['files']!s:>6}{row['issues']!s:>9}"
        )


if __name__ == "__main__":
    typer.run(main)
