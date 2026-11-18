"""Emit stage: turn the repaired lines of one file into the final rows, the side-car and the ledger.

The final file is a tab-separated table (see ``documentation/normalized_cof_spec.md``). Every kept line
starts with its source line number and its page, so the file does not need to keep the source's line
structure: page lines, blank lines and the footer are dropped, lines that are neither headings nor items
(notes, annotations, unknown lines, "DO NOT ORDER" placeholders) go to a side-car file, and the ident
lines are replaced by one canonical ident row. A ledger counts every source line by type and fate.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from cof.common.months import MONTHS
from cof.normalize.classify import LineType
from cof.normalize.context import FileContext
from cof.normalize.ident import canonical_ident
from cof.normalize.items import canonical_fields, parse_date, unquote

COLUMNS = (
    "src_line", "page", "section", "merchandise_flag", "kind", "flag", "sol_code", "text",
    "release_date", "price_designation", "price",
)  # fmt: skip
SIDECAR_COLUMNS = ("src_line", "page", "section", "merchandise_flag", "kind", "text")
PLACEHOLDER = "DO NOT ORDER FROM THIS LINE"
_PAGE = re.compile(r"^PAGE (M-)?(\d+)$")
_SOL = re.compile(r"^([A-Z]{3})(\d\d) (\d{4})$")
_PRICE = re.compile(r"^(?:([A-Z]+): )?(?:\$([\d,]+\.\d\d)|(PI|AR|FREE))$")
_SPACES = re.compile(r"[ \t\r]+")

# Disposition of a source line in the ledger.
KEPT, DROPPED, SIDECAR, REPLACED = "kept", "dropped", "sidecar", "replaced"
_DROPPED_TYPES = {LineType.PAGE, LineType.BLANK, LineType.FOOTER}
_SIDECAR_TYPES = {LineType.NOTE, LineType.ANNOTATION, LineType.UNKNOWN}


class EmitError(Exception):
    """The output cannot be represented (for example, more than ten duplicates of one sol code)."""


@dataclass(frozen=True)
class Row:
    """One row of the final table (and, with fewer columns, of the side-car)."""

    src_line: int  # 1-based source line; 0 for a line that did not exist in the source
    page: int
    section: int
    merchandise_flag: int  # 1 when the page line was "PAGE M-n"
    kind: str  # D ident, H heading, I item (side-car: NOTE, ANNOTATION, UNKNOWN, PLACEHOLDER, UNPARSED_ITEM)
    flag: str = ""
    sol_code: str = ""
    text: str = ""
    release_date: str = ""
    price_designation: str = ""
    price: str = ""

    def fields(self, columns: tuple[str, ...]) -> list[str]:
        """Return the values for the given columns, as text."""
        return [str(getattr(self, c)) for c in columns]


@dataclass
class Emitted:
    """Everything the emit stage produces for one file."""

    rows: list[Row] = field(default_factory=list)
    sidecar: list[Row] = field(default_factory=list)
    ledger: Counter[tuple[str, str]] = field(default_factory=Counter)  # (line type, disposition) -> lines


def collapse(text: str) -> str:
    """Trim a value and turn every run of spaces, tabs and carriage returns into one space."""
    return _SPACES.sub(" ", text).strip()


def split_price(raw: str) -> tuple[str, str]:
    """Split a price field into its designation and its amount.

    ``MSRP: $1,094.99`` gives ``("MSRP", "1094.99")``; a bare ``$4.50`` gives ``("", "4.50")``;
    ``SRP: PI`` and ``SRP: AR`` give ``("SRP", "")``; ``SRP: FREE`` gives ``("SRP", "0.00")``.

    Args:
        raw: The price field after the structural repairs.

    Returns:
        ``(designation, price)``. An unrecognized text is returned as ``("", raw)`` so nothing is lost.
    """
    m = _PRICE.match(collapse(unquote(raw)))
    if m is None:
        return "", raw
    designation, money, status = m.groups()
    if money is not None:
        try:
            return designation or "", f"{Decimal(money.replace(',', '')):.2f}"
        except InvalidOperation:  # pragma: no cover - the pattern only admits digits
            return "", raw
    return designation or "", "0.00" if status == "FREE" else ""


def format_date(raw: str) -> str:
    """Rewrite a ``mm/dd/yy`` release date as ``YYYY-MM-DD`` (every date is in the 2000s).

    Args:
        raw: The date field; empty or an unparseable text is returned unchanged.

    Returns:
        The ISO date, or the input.
    """
    parsed = parse_date(raw)
    return parsed.strftime("%Y-%m-%d") if parsed else raw


class SolCodes:
    """Rewrites sol codes as ``YYYY-MM-nnnn-m``; ``m`` counts repeats of the same code within the file."""

    def __init__(self) -> None:
        """Start with no codes seen."""
        self._seen: Counter[str] = Counter()

    def format(self, raw: str) -> str:
        """Rewrite one sol code.

        Args:
            raw: A sol code such as ``SEP24 0239``.

        Returns:
            ``2024-09-0239-0`` (the next repeat gets ``-1``, and so on), or the input if it is malformed.

        Raises:
            EmitError: If one code occurs more than ten times.
        """
        m = _SOL.match(raw.strip())
        if m is None or m[1] not in MONTHS:
            return raw
        base = f"{2000 + int(m[2])}-{MONTHS.index(m[1]) + 1:02d}-{m[3]}"
        seq = self._seen[base]
        self._seen[base] += 1
        if seq > 9:
            raise EmitError(f"sol code {raw!r} occurs more than ten times")
        return f"{base}-{seq}"


def emit(ctx: FileContext, lines: list[str]) -> Emitted:
    """Build the final rows, the side-car rows and the ledger for one file.

    Args:
        ctx: The decoded and classified source (its types describe ``lines``).
        lines: The repaired lines, one per source line.

    Returns:
        The emitted rows. Every source line is counted exactly once in the ledger.
    """
    out = Emitted()
    sols = SolCodes()
    page, section, merch = 0, 1, 0
    ident_src = [n for n, t in enumerate(ctx.types, start=1) if t == LineType.IDENT]
    out.rows.append(Row(ident_src[0] if ident_src else 0, 0, 1, 0, "D", text=canonical_ident(ctx.month)))
    for number, (line, kind) in enumerate(zip(lines, ctx.types, strict=True), start=1):
        if kind == LineType.PAGE:
            m = _PAGE.match(line.strip())
            assert m is not None  # PAGE lines match by construction
            was_merch, merch, new_page = merch, int(m[1] is not None), int(m[2])
            if new_page < page or (was_merch and not merch):
                section += 1  # the numbering restarted, or the M- pages ended and ordinary numbering resumed
            page = new_page
        if kind == LineType.IDENT:
            out.ledger[kind.value, REPLACED] += 1
        elif kind in _DROPPED_TYPES:
            out.ledger[kind.value, DROPPED] += 1
        elif kind == LineType.HEADING:
            out.rows.append(Row(number, page, section, merch, "H", text=collapse(line)))
            out.ledger[kind.value, KEPT] += 1
        elif kind == LineType.ITEM:
            _emit_item(out, number, line, page, section, merch, sols)
        else:
            assert kind in _SIDECAR_TYPES
            out.sidecar.append(
                Row(number, page, section, merch, kind.value, text=collapse(line.replace("\t", " | ")))
            )
            out.ledger[kind.value, SIDECAR] += 1
    return out


def _emit_item(
    out: Emitted, number: int, line: str, page: int, section: int, merch: int, sols: SolCodes
) -> None:
    """Route one item line to the table or the side-car and count it."""
    fields = line.split("\t")
    canon = canonical_fields(fields)
    if PLACEHOLDER in line:
        out.sidecar.append(
            Row(number, page, section, merch, "PLACEHOLDER", text=collapse(line.replace("\t", " | ")))
        )
        out.ledger["ITEM", SIDECAR] += 1
    elif canon is None:
        out.sidecar.append(
            Row(number, page, section, merch, "UNPARSED_ITEM", text=collapse(line.replace("\t", " | ")))
        )
        out.ledger["ITEM", SIDECAR] += 1
    else:
        designation, price = split_price(canon[4])
        out.rows.append(
            Row(
                number, page, section, merch, "I",
                flag=collapse(canon[0]).upper(), sol_code=sols.format(collapse(canon[1])).upper(),
                text=collapse(canon[2]), release_date=format_date(collapse(canon[3])),
                price_designation=designation.upper(), price=price,
            )
        )  # fmt: skip
        out.ledger["ITEM", KEPT] += 1


def render(columns: tuple[str, ...], rows: list[Row]) -> str:
    """Render rows as tab-separated text with a header row and a single final newline.

    Args:
        columns: Column names, in order.
        rows: The rows.

    Returns:
        The text.

    Raises:
        EmitError: If a value holds a tab or a line break, which would corrupt the table.
    """
    out = ["\t".join(columns)]
    for row in rows:
        values = row.fields(columns)
        if any(c in v for v in values for c in "\t\n\r"):
            raise EmitError(f"line {row.src_line}: a value contains a tab or line break")
        out.append("\t".join(values))
    return "\n".join(out) + "\n"
