"""Fixers: the automatic repairs of the normalizer, one change recorded per repair.

Only the rules classed ``auto-lossless`` or ``auto-derived`` in ``config/rules.yaml`` are repaired here.
A repair never adds, removes or reorders lines.
"""

from dataclasses import dataclass

from cof.normalize.classify import LineType
from cof.normalize.context import FileContext
from cof.normalize.ident import corrected_line, expected_for, month_mismatch, number_mismatch, parse_ident
from cof.normalize.items import (
    DATE_LONG_RE,
    PRICE_NOSPACE_RE,
    SOL_LEGACY_SPLIT_RE,
    SOL_NOSPACE_RE,
    TAIL,
    canonical_fields,
    is_quoted,
    layout_of,
    parse_date,
    unquote,
)


@dataclass(frozen=True)
class Change:
    """One repair made to a line."""

    rule_id: str
    line: int  # 1-based
    before: str
    after: str
    how: str


def fix_item(number: int, line: str, changes: list[Change]) -> str:
    """Repair one item line.

    Args:
        number: 1-based line number (for the change records).
        line: The item line.
        changes: List that receives one :class:`Change` per repair.

    Returns:
        The repaired line; unchanged if its layout is unknown or it is a placeholder.
    """
    fields = line.split("\t")
    layout = layout_of(fields)
    canon = canonical_fields(fields)
    if canon is None:  # unknown layout or placeholder: keep as published
        return line
    layout_rules = {
        "B": ("I01", f"{len(fields)} fields", "added the empty trailing field"),
        "C": ("I02", f"{len(fields)} fields", "dropped the empty field after the sol code"),
        "D": ("I03", f"{len(fields)} fields", "inserted an empty release date"),
    }
    if layout in layout_rules:
        rule, before, how = layout_rules[layout]
        changes.append(Change(rule, number, before, "7 fields", how))
    for index, value in enumerate(canon):  # CSV quoting: "..." becomes ..., "" becomes "
        if is_quoted(value):
            canon[index] = unquote(value)
            changes.append(
                Change("I20", number, value, canon[index], f"removed CSV quoting from field {index}")
            )
    if SOL_NOSPACE_RE.match(canon[1].strip()):
        fixed = canon[1].strip()[:5] + " " + canon[1].strip()[5:]
        changes.append(Change("I05", number, canon[1], fixed, "inserted the space in the sol code"))
        canon[1] = fixed
    if SOL_LEGACY_SPLIT_RE.match(canon[1].strip()):
        fixed = canon[1].strip().replace(" ", "")  # only the space goes; every digit is kept
        changes.append(
            Change("I22", number, canon[1], fixed, "removed the space in the legacy STAR sol code")
        )
        canon[1] = fixed
    if canon[2] != canon[2].strip():
        changes.append(Change("I14", number, canon[2], canon[2].strip(), "trimmed the item text"))
        canon[2] = canon[2].strip()
    if DATE_LONG_RE.match(canon[3]):
        parsed = parse_date(canon[3])
        if parsed is not None:
            fixed = parsed.strftime("%m/%d/%y")
            changes.append(Change("I11", number, canon[3], fixed, "rewrote the date as mm/dd/yy"))
            canon[3] = fixed
    if canon[4] != canon[4].strip():
        changes.append(Change("I19", number, canon[4], canon[4].strip(), "trimmed the price"))
        canon[4] = canon[4].strip()
    if PRICE_NOSPACE_RE.match(canon[4]):
        fixed = canon[4].replace(":", ": ", 1)
        changes.append(Change("I09", number, canon[4], fixed, "inserted the space after the colon"))
        canon[4] = fixed
    if canon[5] != TAIL or canon[6] != "":
        changes.append(
            Change("I04", number, f"{canon[5]!r}+{canon[6]!r}", repr(TAIL) + "+''", "standard tail")
        )
        canon[5], canon[6] = TAIL, ""
    return "\t".join(canon)


def fix_ident(number: int, line: str, month: str, changes: list[Change]) -> str:
    """Correct the month, year, volume and issue of an ident line from the file name.

    Args:
        number: 1-based line number.
        line: The ident line.
        month: Month code of the file, e.g. ``"JAN13"``.
        changes: List that receives the changes.

    Returns:
        The corrected line, or the line unchanged if it already agrees with the file name.
    """
    parts = parse_ident(line)
    if parts is None:
        return line
    exp = expected_for(month)
    fixed = corrected_line(parts, exp)
    if fixed != line.strip(" \t"):
        for rule, problem in (("F07", month_mismatch(parts, exp)), ("F08", number_mismatch(parts, exp))):
            if problem:
                changes.append(Change(rule, number, line.strip(" \t"), fixed, problem))
        return fixed
    return line


def apply_fixes(ctx: FileContext) -> tuple[list[str], list[Change]]:
    """Repair every automatically fixable defect in a file.

    Args:
        ctx: The decoded, classified file.

    Returns:
        ``(new_lines, changes)``; ``new_lines`` has exactly as many lines as the input.
    """
    changes: list[Change] = []
    out: list[str] = []
    for number, (line, kind) in enumerate(zip(ctx.lines, ctx.types, strict=True), start=1):
        if kind != LineType.ITEM and line != line.rstrip(" \t"):
            changes.append(Change("L01", number, repr(line[-12:]), repr(line.rstrip(" \t")[-12:]), "trimmed"))
            line = line.rstrip(" \t")
        if kind == LineType.IDENT:
            line = fix_ident(number, line, ctx.month, changes)
        elif kind == LineType.ITEM:
            line = fix_item(number, line, changes)
        out.append(line)
    return out, changes
