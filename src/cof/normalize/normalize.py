"""Normalize one COF text file: decode, repair, validate, and account for every issue found."""

from dataclasses import dataclass, field, replace

from pydantic import BaseModel

from cof.common.months import to_period
from cof.normalize.classify import LineType
from cof.normalize.context import FileContext, Issue, build_context
from cof.normalize.detectors import first_catalog_item_number
from cof.normalize.emit import COLUMNS, SIDECAR_COLUMNS, Emitted, emit, render
from cof.normalize.fixers import Change, apply_fixes
from cof.normalize.ident import ident_facts
from cof.normalize.rules import Rule, detect_all


class Patch(BaseModel):
    """A reviewed edit of one line (``config/patches.yaml``)."""

    month: str
    line: int
    old: str
    new: str
    reason: str


class NormalizationError(Exception):
    """A post-condition failed: the normalizer or its rules are inconsistent."""


@dataclass(frozen=True)
class IssueRecord:
    """The fate of one issue found in a file."""

    rule_id: str
    line: int | None
    rule_class: str
    status: str  # "fixed", "patched", "open" or "info"
    before: str
    after: str
    how: str
    evidence: str


@dataclass(frozen=True)
class NormalizedFile:
    """The result of normalizing one file."""

    month: str
    period: str  # YYYY_MM
    text: str | None  # the final table (header row plus rows), or None when the file was rejected
    status: str  # "ok" or "rejected"
    encoding: str
    compression: str
    eol: str
    source_lines: int
    output_rows: int  # rows in the final table, without the header row
    non_ascii_bytes: int
    records: list[IssueRecord] = field(default_factory=list)
    sidecar: str | None = None  # the side-car table, or None when there is nothing to put in it
    sidecar_rows: int = 0
    ledger: dict[tuple[str, str], int] = field(default_factory=dict)  # (line type, fate) -> source lines
    ident: dict[str, str] = field(default_factory=dict)  # facts for idents.csv

    def count(self, status: str) -> int:
        """Number of issue records with a status."""
        return sum(1 for r in self.records if r.status == status)


def _render(lines: list[str]) -> str:
    """Join lines with LF and end the text with exactly one LF."""
    return "\n".join(lines) + "\n" if lines else ""


def normalize_file(
    month: str,
    data: bytes,
    rules: dict[str, Rule],
    patches: list[Patch] | None = None,
    full_checks: bool = True,
) -> NormalizedFile:
    """Normalize one file and verify the result.

    Args:
        month: Month code from the source file name.
        data: Raw bytes of the selected version, as downloaded.
        rules: The rule registry (``config/rules.yaml``).
        patches: Reviewed edits; only those for ``month`` are used.
        full_checks: Also run the rules marked ``optional`` in ``config/rules.yaml``.

    Returns:
        The final table, the side-car, the ledger and a record for every issue found. A file that is not a
        COF text file (F01) is rejected: ``text`` is ``None``.

    Raises:
        NormalizationError: If a patch is stale, or a post-condition fails (the repair stage changed the
            line count, a rule repaired automatically is still detected, the repair is not stable, a source
            line is missing from the ledger, or the table does not read back).
    """
    ctx = build_context(month, data)
    before_issues = detect_all(ctx, full_checks)
    if any(i.rule_id == "F01" for i in before_issues):
        rejected = [
            _record(i, rules, "open", "", "", "file rejected: " + rules[i.rule_id].fix) for i in before_issues
        ]
        return _result(ctx, month, None, "rejected", 0, rejected)

    lines, changes = apply_fixes(ctx)
    for patch in (p for p in patches or [] if p.month == month):
        if lines[patch.line - 1] != patch.old:
            raise NormalizationError(
                f"{month} line {patch.line}: patch is stale (line is {lines[patch.line - 1]!r})"
            )
        lines[patch.line - 1] = patch.new
        changes.append(Change("PATCH", patch.line, patch.old, patch.new, patch.reason))
    text = _render(lines)  # the repaired source text (an intermediate form; the final table is built below)

    # Post-conditions of the repair stage: same number of lines; nothing repairable is left; it is stable.
    if len(lines) != len(ctx.lines):
        raise NormalizationError(f"{month}: line count changed from {len(ctx.lines)} to {len(lines)}")
    after = build_context(month, text.encode("utf-8"))
    after_issues = detect_all(after, full_checks)
    still = [i for i in after_issues if rules[i.rule_id].rule_class.startswith("auto-")]
    if still:
        raise NormalizationError(f"{month}: rules repaired automatically are still detected: {still[:3]}")
    again = _render(apply_fixes(after)[0])
    if again != text:
        raise NormalizationError(f"{month}: normalizing the output changes it (not idempotent)")

    after_keys = {(i.rule_id, i.line) for i in after_issues}
    by_key: dict[tuple[str, int | None], Change] = {(c.rule_id, c.line): c for c in changes}
    out_records: list[IssueRecord] = []
    for issue in before_issues:
        rule = rules[issue.rule_id]
        change = by_key.get((issue.rule_id, issue.line))
        if rule.rule_class.startswith("auto-"):
            how = change.how if change else rule.fix
            out_records.append(
                _record(
                    issue,
                    rules,
                    "fixed",
                    change.before if change else "",
                    change.after if change else "",
                    how,
                )
            )
        elif rule.rule_class == "info":
            out_records.append(_record(issue, rules, "info", "", "", rule.fix))
        elif (issue.rule_id, issue.line) not in after_keys:
            patch_change = next((c for c in changes if c.rule_id == "PATCH" and c.line == issue.line), None)
            out_records.append(
                _record(issue, rules, "patched", patch_change.before if patch_change else "",
                        patch_change.after if patch_change else "", patch_change.how if patch_change else "")
            )  # fmt: skip
        else:
            out_records.append(_record(issue, rules, "open", "", "", rule.fix))
    # Emit from the context of the repaired text, so a patch that changes a line's type (for example a
    # damaged PAGE line) is classified as the patched line, not as the original.
    emitted = emit(after, lines)
    table = _checked_table(month, ctx, emitted)
    ident_lines = [text for _, text in ctx.typed_lines(LineType.IDENT)]
    return replace(
        _result(ctx, month, table, "ok", len(emitted.rows), out_records),
        sidecar=render(SIDECAR_COLUMNS, emitted.sidecar) if emitted.sidecar else None,
        sidecar_rows=len(emitted.sidecar),
        ledger=dict(emitted.ledger),
        ident=ident_facts(month, ident_lines, first_catalog_item_number(ctx)),
    )


def _checked_table(month: str, ctx: FileContext, emitted: Emitted) -> str:
    """Render the final table and verify the ledger and the read-back.

    Raises:
        NormalizationError: If a source line is not accounted for exactly once, or the rendered table does
            not read back to the same rows.
    """
    counted = sum(emitted.ledger.values())
    if counted != len(ctx.lines):
        raise NormalizationError(f"{month}: ledger counts {counted} lines, the source has {len(ctx.lines)}")
    kept = sum(n for (_, fate), n in emitted.ledger.items() if fate == "kept")
    if len(emitted.rows) != kept + 1:  # every kept line is one row; plus the canonical ident row
        raise NormalizationError(f"{month}: {len(emitted.rows)} rows for {kept} kept lines")
    table = render(COLUMNS, emitted.rows)
    back = [line.split("\t") for line in table.splitlines()]
    if back[0] != list(COLUMNS) or any(len(r) != len(COLUMNS) for r in back):
        raise NormalizationError(f"{month}: the table does not read back with {len(COLUMNS)} columns")
    if [r[0] for r in back[1:]] != [str(row.src_line) for row in emitted.rows]:
        raise NormalizationError(f"{month}: the table does not read back to the same rows")
    return table


def _record(
    issue: Issue, rules: dict[str, Rule], status: str, before: str, after: str, how: str
) -> IssueRecord:
    """Build the record of one issue."""
    return IssueRecord(
        rule_id=issue.rule_id,
        line=issue.line,
        rule_class=rules[issue.rule_id].rule_class,
        status=status,
        before=before,
        after=after,
        how=how,
        evidence=issue.evidence,
    )


def _result(
    ctx: FileContext, month: str, text: str | None, status: str, output_rows: int, records: list[IssueRecord]
) -> NormalizedFile:
    """Assemble a :class:`NormalizedFile` from the source context and the outcome."""
    return NormalizedFile(
        month=month,
        period=to_period(month),
        text=text,
        status=status,
        encoding=ctx.decoded.encoding,
        compression=ctx.decoded.compression,
        eol=ctx.decoded.eol,
        source_lines=len(ctx.lines),
        output_rows=output_rows,
        non_ascii_bytes=ctx.decoded.non_ascii_bytes,
        records=records,
    )
