"""Detectors: one function per rule in ``config/rules.yaml``. Importing this module registers them all."""

import re
from collections import Counter
from collections.abc import Iterator

from cof.normalize.classify import LineType
from cof.normalize.context import FileContext, Issue
from cof.normalize.ident import (
    expected_for,
    month_mismatch,
    number_mismatch,
    parse_ident,
)
from cof.normalize.items import (
    DATE_LONG_RE,
    DATE_RE,
    KNOWN_FLAGS,
    PRICE_NOSPACE_RE,
    PRICE_RE,
    SOL_NOSPACE_RE,
    SOL_STRICT_RE,
    TAIL,
    canonical_fields,
    is_quoted,
    layout_of,
    parse_date,
    unquote,
)
from cof.normalize.rules import detector, rule_param

_HEADER_ROW_RE = re.compile(r"[A-Za-z]+(?:\t[A-Za-z]+){3,}")
_DAMAGED_PAGE_RE = re.compile(r"^(?:P|PA|PAG|AGE|GE|E) ?(?:M-)?\d+$")


def _items(ctx: FileContext) -> Iterator[tuple[int, list[str]]]:
    """Yield ``(line number, tab-split fields)`` for every item line."""
    for number, text in ctx.typed_lines(LineType.ITEM):
        yield number, text.split("\t")


def _canonical_items(ctx: FileContext) -> Iterator[tuple[int, list[str]]]:
    """Yield ``(line number, canonical 7 fields)`` for item lines whose layout is known."""
    for number, fields in _items(ctx):
        canon = canonical_fields(fields)
        if canon is not None:
            yield number, canon


# ---- file level ---------------------------------------------------------------------------------


@detector("F01")
def foreign_layout(ctx: FileContext) -> Iterator[Issue]:
    """Report a file whose first line is a header row of column names (not a COF text file)."""
    first = next((line for line in ctx.lines if line.strip()), "")
    if _HEADER_ROW_RE.fullmatch(first):
        yield Issue("F01", 1, f"header row: {first[:80]!r}")


@detector("F02")
def mixed_line_endings(ctx: FileContext) -> Iterator[Issue]:
    """Report a file with both CRLF and LF line endings."""
    if ctx.decoded.eol == "mixed":
        yield Issue("F02", None, "CRLF and LF both present")


@detector("F03")
def bare_carriage_return(ctx: FileContext) -> Iterator[Issue]:
    """Report each line with a carriage return inside it."""
    for number in ctx.decoded.bare_cr_lines:
        yield Issue("F03", number, "carriage return inside the line")


@detector("F04")
def undefined_cp1252_byte(ctx: FileContext) -> Iterator[Issue]:
    """Report each line holding a byte that Windows-1252 leaves undefined."""
    for number in ctx.decoded.undefined_byte_lines:
        yield Issue("F04", number, "byte undefined in Windows-1252")


@detector("F05")
def truncated_gzip(ctx: FileContext) -> Iterator[Issue]:
    """Report a gzip stream that ended early."""
    if ctx.decoded.compression == "gzip-truncated":
        yield Issue("F05", None, f"recovered {len(ctx.lines)} lines before the stream ended")


@detector("F06")
def ident_missing(ctx: FileContext) -> Iterator[Issue]:
    """Report a file with no identification line."""
    if ctx.lines and not ctx.typed_lines(LineType.IDENT):
        yield Issue("F06", None, "no identification line before the first PAGE line")


@detector("F07")
def ident_month_mismatch(ctx: FileContext) -> Iterator[Issue]:
    """Report an identification line naming a different month (or year) than the file name."""
    exp = expected_for(ctx.month)
    for number, text in ctx.typed_lines(LineType.IDENT):
        parts = parse_ident(text)
        problem = month_mismatch(parts, exp) if parts else None
        if problem:
            yield Issue("F07", number, problem)


@detector("F08")
def ident_volume_issue_mismatch(ctx: FileContext) -> Iterator[Issue]:
    """Report volume/issue numbers that differ from those derived from the file name.

    Volume is the year minus 1990 and the issue within the volume is the month number; the catalog issue
    number is ``(volume - 1) * 12 + month + 27`` (verified only for JUN19 to MAR20).
    """
    exp = expected_for(ctx.month)
    for number, text in ctx.typed_lines(LineType.IDENT):
        parts = parse_ident(text)
        problem = number_mismatch(parts, exp) if parts else None
        if problem:
            yield Issue("F08", number, problem)


@detector("F09")
def footer_missing(ctx: FileContext) -> Iterator[Issue]:
    """Report a file whose last non-blank line is not a bare number."""
    if ctx.lines and LineType.FOOTER not in ctx.types:
        yield Issue("F09", None, "last non-blank line is not a bare number")


@detector("F10")
def empty_file(ctx: FileContext) -> Iterator[Issue]:
    """Report a file with no lines."""
    if not ctx.lines:
        yield Issue("F10", None, "no lines")


# ---- line level ---------------------------------------------------------------------------------


@detector("L01")
def trailing_whitespace_non_item(ctx: FileContext) -> Iterator[Issue]:
    """Report non-item lines padded with trailing tabs or spaces (including whitespace-only lines)."""
    for number, (text, kind) in enumerate(zip(ctx.lines, ctx.types, strict=True), start=1):
        if kind != LineType.ITEM and text != text.rstrip(" \t"):
            yield Issue("L01", number, f"{kind.value} line ends with whitespace: {text[-12:]!r}")


@detector("L02")
def page_line_damaged(ctx: FileContext) -> Iterator[Issue]:
    """Report lines that look like a PAGE line with its first characters missing."""
    for number, text in ctx.typed_lines(LineType.HEADING):
        if _DAMAGED_PAGE_RE.match(text.strip(" \t")):
            yield Issue("L02", number, text.strip(" \t"))


@detector("L03")
def page_number_jump(ctx: FileContext) -> Iterator[Issue]:
    """Report a PAGE number far above the previous one (backwards moves are section restarts, not issues)."""
    max_jump = int(rule_param("L03", "max_jump"))
    previous = 0
    for number, text in ctx.typed_lines(LineType.PAGE):
        page = int(re.sub(r"\D", "", text.split()[-1].split("-")[-1]))
        if page - previous > max_jump:
            yield Issue("L03", number, f"{text.strip(' \t')} after page {previous}")
        previous = page


@detector("L04")
def note_line(ctx: FileContext) -> Iterator[Issue]:
    """Report each NOTE line."""
    for number, text in ctx.typed_lines(LineType.NOTE):
        yield Issue("L04", number, text[:80])


@detector("L05")
def annotation_line(ctx: FileContext) -> Iterator[Issue]:
    """Report each bracketed annotation line."""
    for number, text in ctx.typed_lines(LineType.ANNOTATION):
        yield Issue("L05", number, text[:80])


@detector("L06")
def hand_added_line(ctx: FileContext) -> Iterator[Issue]:
    """Report "DO NOT ORDER FROM THIS LINE" placeholder items (publisher text, not a hand edit)."""
    for number, text in ctx.typed_lines(LineType.ITEM):
        if "DO NOT ORDER FROM THIS LINE" in text:
            yield Issue("L06", number, text.strip()[:80])


@detector("L07")
def unclassified_line(ctx: FileContext) -> Iterator[Issue]:
    """Report lines of no known type (other than stray numbers)."""
    for number, text in ctx.typed_lines(LineType.UNKNOWN):
        if not text.strip(" \t").isdigit():
            yield Issue("L07", number, text[:80])


@detector("L08")
def numeric_only_line(ctx: FileContext) -> Iterator[Issue]:
    """Report lines that hold only a number and are not the footer."""
    for number, text in ctx.typed_lines(LineType.UNKNOWN):
        if text.strip(" \t").isdigit():
            yield Issue("L08", number, text.strip(" \t"))


# ---- item level ---------------------------------------------------------------------------------


@detector("I01")
def layout_b(ctx: FileContext) -> Iterator[Issue]:
    """Report item lines without the trailing empty field."""
    for number, fields in _items(ctx):
        if layout_of(fields) == "B":
            yield Issue("I01", number, "6 fields, no trailing empty field")


@detector("I02")
def layout_c(ctx: FileContext) -> Iterator[Issue]:
    """Report item lines with an extra empty field after the sol code."""
    for number, fields in _items(ctx):
        if layout_of(fields) == "C":
            yield Issue("I02", number, "8 fields, empty field 2")


@detector("I03")
def layout_d(ctx: FileContext) -> Iterator[Issue]:
    """Report item lines with no release-date field."""
    for number, fields in _items(ctx):
        if layout_of(fields) == "D":
            yield Issue("I03", number, "6 fields, no date field")


@detector("I04")
def tail_variant(ctx: FileContext) -> Iterator[Issue]:
    """Report item lines whose ending is not ' = $' plus an empty field."""
    for number, canon in _canonical_items(ctx):
        if canon[5] != TAIL or canon[6] != "":
            yield Issue("I04", number, f"tail {canon[5]!r}+{canon[6]!r}")


@detector("I05")
def sol_code_no_space(ctx: FileContext) -> Iterator[Issue]:
    """Report sol codes written without the space."""
    for number, canon in _canonical_items(ctx):
        if SOL_NOSPACE_RE.match(canon[1].strip()):
            yield Issue("I05", number, canon[1])


@detector("I06")
def sol_code_malformed(ctx: FileContext) -> Iterator[Issue]:
    """Report sol codes that match neither the standard nor the no-space form."""
    for number, canon in _canonical_items(ctx):
        sol = canon[1].strip()
        if not SOL_STRICT_RE.match(sol) and not SOL_NOSPACE_RE.match(sol):
            yield Issue("I06", number, sol)


@detector("I07")
def sol_month_mismatch(ctx: FileContext) -> Iterator[Issue]:
    """Report sol codes whose month and year differ from the file name."""
    for number, canon in _canonical_items(ctx):
        sol = canon[1].strip()
        if (SOL_STRICT_RE.match(sol) or SOL_NOSPACE_RE.match(sol)) and sol[:5] != ctx.month:
            yield Issue("I07", number, f"{sol} in file {ctx.month}")


@detector("I08")
def sol_duplicate(ctx: FileContext) -> Iterator[Issue]:
    """Report the second and later occurrences of a sol code."""
    counts = Counter(canon[1].strip().replace(" ", "") for _, canon in _canonical_items(ctx))
    seen: set[str] = set()
    for number, canon in _canonical_items(ctx):
        key = canon[1].strip().replace(" ", "")
        if counts[key] > 1 and key in seen:
            yield Issue("I08", number, canon[1])
        seen.add(key)


@detector("I09")
def price_no_space(ctx: FileContext) -> Iterator[Issue]:
    """Report prices with no space after the colon."""
    for number, canon in _canonical_items(ctx):
        if PRICE_NOSPACE_RE.match(unquote(canon[4]).strip()):
            yield Issue("I09", number, canon[4])


@detector("I10")
def price_unrecognized(ctx: FileContext) -> Iterator[Issue]:
    """Report prices outside every known form (surrounding whitespace is ignored; see I19)."""
    for number, canon in _canonical_items(ctx):
        price = unquote(canon[4]).strip()
        if not PRICE_RE.match(price) and not PRICE_NOSPACE_RE.match(price):
            yield Issue("I10", number, repr(canon[4]))


@detector("I11")
def date_four_digit_year(ctx: FileContext) -> Iterator[Issue]:
    """Report dates written with a four-digit year or without zero padding."""
    for number, canon in _canonical_items(ctx):
        if DATE_LONG_RE.match(canon[3]) and parse_date(canon[3]) is not None:
            yield Issue("I11", number, canon[3])


@detector("I12")
def date_invalid(ctx: FileContext) -> Iterator[Issue]:
    """Report dates that are neither empty nor valid in a known form."""
    for number, canon in _canonical_items(ctx):
        date = canon[3]
        if date and not DATE_RE.match(date) and not DATE_LONG_RE.match(date):
            yield Issue("I12", number, repr(date))
        elif date and parse_date(date) is None:
            yield Issue("I12", number, f"not a calendar date: {date}")


@detector("I13")
def flag_unknown(ctx: FileContext) -> Iterator[Issue]:
    """Report flag values outside the known set."""
    for number, canon in _canonical_items(ctx):
        if canon[0].strip() not in KNOWN_FLAGS:
            yield Issue("I13", number, repr(canon[0]))


@detector("I14")
def text_edge_whitespace(ctx: FileContext) -> Iterator[Issue]:
    """Report item text with leading or trailing whitespace."""
    for number, canon in _canonical_items(ctx):
        if canon[2] != canon[2].strip():
            yield Issue("I14", number, repr(canon[2][:12] + "..." + canon[2][-8:]))


@detector("I15")
def text_replacement_char(ctx: FileContext) -> Iterator[Issue]:
    """Report any line containing the Unicode replacement character."""
    for number, text in enumerate(ctx.lines, start=1):
        if "�" in text:
            yield Issue("I15", number, text.strip()[:80])


@detector("I16")
def item_field_count(ctx: FileContext) -> Iterator[Issue]:
    """Report item lines that fit no known layout."""
    for number, fields in _items(ctx):
        if layout_of(fields) == "X":
            yield Issue("I16", number, f"{len(fields)} fields")


@detector("I17")
def text_unbalanced_parens(ctx: FileContext) -> Iterator[Issue]:
    """Report item text with unequal numbers of opening and closing parentheses."""
    for number, canon in _canonical_items(ctx):
        if canon[2].count("(") != canon[2].count(")"):
            yield Issue("I17", number, canon[2][-60:])


@detector("I18")
def text_double_space(ctx: FileContext) -> Iterator[Issue]:
    """Report item text with two consecutive spaces."""
    for number, canon in _canonical_items(ctx):
        if "  " in canon[2].strip():
            yield Issue("I18", number, canon[2][:60])


@detector("I19")
def price_edge_whitespace(ctx: FileContext) -> Iterator[Issue]:
    """Report prices with leading or trailing whitespace (for example ``'SRP: PI '``)."""
    for number, canon in _canonical_items(ctx):
        price = unquote(canon[4])
        if price != price.strip():
            yield Issue("I19", number, repr(canon[4]))


@detector("I20")
def csv_quoted_field(ctx: FileContext) -> Iterator[Issue]:
    """Report fields wrapped in CSV-style quotes (used when a field holds a comma or a quote mark)."""
    for number, canon in _canonical_items(ctx):
        for index, value in enumerate(canon):
            if is_quoted(value):
                yield Issue("I20", number, f"field {index}: {value[:60]}")


@detector("I21")
def price_no_designation(ctx: FileContext) -> Iterator[Issue]:
    """Report prices without an SRP or MSRP designation (bare ``$n.nn`` or bare ``PI``)."""
    for number, canon in _canonical_items(ctx):
        price = unquote(canon[4]).strip()
        if PRICE_RE.match(price) and "SRP" not in price:
            yield Issue("I21", number, price)


_CATALOG_ITEM_RE = re.compile(r"^PREVIEWS #(\d+) [A-Z]+ \d{4}\b")


def first_catalog_item_number(ctx: FileContext) -> int | None:
    """Return the number in the first ``PREVIEWS #nnn <MONTH> <YEAR>`` item, or None if there is none."""
    for _, fields in _items(ctx):
        if len(fields) > 2 and (m := _CATALOG_ITEM_RE.match(fields[2].strip().strip('"'))):
            return int(m[1])
    return None


@detector("F11")
def catalog_number_mismatch(ctx: FileContext) -> Iterator[Issue]:
    """Report a first PREVIEWS item whose catalog number (minus 2) differs from the derived number."""
    found = first_catalog_item_number(ctx)
    expected = expected_for(ctx.month).catalog
    if found is not None and found - 2 != expected:
        yield Issue(
            "F11", None, f"first PREVIEWS item is #{found}; derived from the file name: #{expected + 2}"
        )
