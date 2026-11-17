"""Identification ("ident") lines: parsing, the values expected from a file name, and correction.

Variants (spec section 2.1):

* ``A``  ``PREVIEWS <MONTH> VOL. nn #n``
* ``B``  ``[PREVIEWS ]<MONTH> Vnn #n``  (also the second line of the terse ``ORDER FORM`` form)
* ``D1`` ``PREVIEWS <MONTH> YYYY``
* ``D2`` ``ISSUE #nnn (VOL. nn #n)``

The file name is authoritative for the period: volume = year - 1990, issue in volume = month number, and
catalog issue number = (volume - 1) * 12 + month + 27 (verified only for JUN19 to MAR20).
"""

import re
from dataclasses import dataclass

from cof.common.months import MONTHS

MONTH_NAMES: tuple[str, ...] = (
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
)  # fmt: skip
_A = re.compile(r"^PREVIEWS ([A-Z]+) VOL\. (\d+) #(\d+)$")
_B = re.compile(r"^(PREVIEWS )?([A-Z]+) V(\d+) #(\d+)$")
_D1 = re.compile(r"^PREVIEWS ([A-Z]+) (\d{4})$")
_D2 = re.compile(r"^ISSUE #(\d+) \(VOL\. (\d+) #(\d+)\)$")


@dataclass(frozen=True)
class IdentParts:
    """The parts of a parsed ident line (fields not present in a variant are ``None``)."""

    variant: str  # "A", "B", "D1" or "D2"
    month_word: str | None = None
    year: int | None = None
    volume: int | None = None
    issue: int | None = None
    catalog: int | None = None
    prefix: str = ""  # "PREVIEWS " for variant B when present


@dataclass(frozen=True)
class Expected:
    """The ident values implied by a file name."""

    month: int  # 0-based
    year: int
    volume: int
    issue: int
    catalog: int


def month_number(word: str) -> int | None:
    """Return the 0-based month for a month name or 3-letter code, or None."""
    if word in MONTH_NAMES:
        return MONTH_NAMES.index(word)
    return MONTHS.index(word) if word in MONTHS else None


def expected_for(month_code: str) -> Expected:
    """Compute the ident values for a file name such as ``JAN13``.

    Args:
        month_code: Month code from the file name.

    Returns:
        The expected month, year, volume, issue in volume and catalog issue number.
    """
    month = MONTHS.index(month_code[:3])
    year = 2000 + int(month_code[3:])
    volume = year - 1990
    return Expected(month, year, volume, month + 1, (volume - 1) * 12 + (month + 1) + 27)


def parse_ident(line: str) -> IdentParts | None:
    """Parse an ident line.

    Args:
        line: One line (surrounding spaces and tabs are ignored).

    Returns:
        The parts, or ``None`` if the line is not in a known ident form.
    """
    s = line.strip(" \t")
    if m := _A.match(s):
        return IdentParts("A", month_word=m[1], volume=int(m[2]), issue=int(m[3]))
    if m := _B.match(s):
        return IdentParts("B", month_word=m[2], volume=int(m[3]), issue=int(m[4]), prefix=m[1] or "")
    if m := _D1.match(s):
        return IdentParts("D1", month_word=m[1], year=int(m[2]))
    if m := _D2.match(s):
        return IdentParts("D2", catalog=int(m[1]), volume=int(m[2]), issue=int(m[3]))
    return None


def month_mismatch(parts: IdentParts, exp: Expected) -> str | None:
    """Describe a wrong month or year in an ident line, or return None if it is right."""
    if parts.month_word is not None and month_number(parts.month_word) != exp.month:
        return f"ident month {parts.month_word}, file name {MONTHS[exp.month]}"
    if parts.year is not None and parts.year != exp.year:
        return f"ident year {parts.year}, file name {exp.year}"
    return None


def number_mismatch(parts: IdentParts, exp: Expected) -> str | None:
    """Describe wrong volume/issue numbers in an ident line, or return None if they are right."""
    if parts.variant in ("A", "B") and (parts.volume, parts.issue) != (exp.volume, exp.issue):
        return f"ident vol/issue {parts.volume}/{parts.issue}, expected {exp.volume}/{exp.issue}"
    if parts.variant == "D2" and (parts.catalog, parts.volume, parts.issue) != (
        exp.catalog,
        exp.volume,
        exp.issue,
    ):
        got = (parts.catalog, parts.volume, parts.issue)
        return f"ident {got}, expected {(exp.catalog, exp.volume, exp.issue)}"
    return None


def corrected_line(parts: IdentParts, exp: Expected) -> str:
    """Render an ident line with month, year, volume and issue taken from the file name.

    The published style is kept: a spelled-out month stays spelled out, a 3-letter month stays 3 letters.

    Args:
        parts: The parsed line.
        exp: Values implied by the file name.

    Returns:
        The corrected line.
    """
    word = parts.month_word
    if word is not None and month_number(word) != exp.month:
        word = MONTH_NAMES[exp.month] if word in MONTH_NAMES else MONTHS[exp.month]
    if parts.variant == "A":
        return f"PREVIEWS {word} VOL. {exp.volume} #{exp.issue}"
    if parts.variant == "B":
        return f"{parts.prefix}{word} V{exp.volume} #{exp.issue}"
    if parts.variant == "D1":
        return f"PREVIEWS {word} {exp.year}"
    return f"ISSUE #{exp.catalog} (VOL. {exp.volume} #{exp.issue})"


def canonical_ident(month_code: str) -> str:
    """Render the one ident line every normalized file gets, derived from the file name.

    Args:
        month_code: Month code from the file name, for example ``"MAR15"``.

    Returns:
        ``PREVIEWS <MONTH> <YYYY> ISSUE #<catalog> (VOL. <volume> #<issue>)``.
    """
    exp = expected_for(month_code)
    return (
        f"PREVIEWS {MONTH_NAMES[exp.month]} {exp.year} ISSUE #{exp.catalog} (VOL. {exp.volume} #{exp.issue})"
    )


def _yes_no(ok: bool | None) -> str:
    """Render a check result: ``yes``, ``no`` or empty when the check does not apply."""
    return "" if ok is None else ("yes" if ok else "no")


def ident_facts(month_code: str, ident_lines: list[str], item_catalog: int | None) -> dict[str, str]:
    """Collect what the file says about its own identity and compare it with the file name.

    Args:
        month_code: Month code from the file name.
        ident_lines: The source ident lines (zero, one or two), as published.
        item_catalog: Number from the first ``PREVIEWS #nnn`` item, or ``None``.

    Returns:
        One flat record for ``idents.csv``: what was found, what the file name implies, and one
        ``yes``/``no``/empty check per comparison.
    """
    exp = expected_for(month_code)
    found: dict[str, int | None] = dict.fromkeys(("month", "year", "volume", "issue", "catalog"))
    variants: list[str] = []
    for line in ident_lines:
        parts = parse_ident(line)
        if parts is None:
            continue
        variants.append(parts.variant)
        if parts.month_word is not None:
            found["month"] = month_number(parts.month_word)
        for key in ("year", "volume", "issue", "catalog"):
            value = getattr(parts, key)
            if value is not None:
                found[key] = value
    month, year, volume, issue, catalog = (found[k] for k in ("month", "year", "volume", "issue", "catalog"))
    year_from = year if year is not None else (1990 + volume if volume is not None else None)
    return {
        "ident_present": "yes" if ident_lines else "no",
        "ident_lines": " | ".join(line.strip(" \t") for line in ident_lines),
        "ident_variant": "+".join(variants),
        "ident_month": "" if month is None else str(month + 1),
        "ident_year": "" if year is None else str(year),
        "ident_volume": "" if volume is None else str(volume),
        "ident_issue": "" if issue is None else str(issue),
        "ident_catalog": "" if catalog is None else str(catalog),
        "expected_year": str(exp.year),
        "expected_month": str(exp.month + 1),
        "expected_volume": str(exp.volume),
        "expected_issue": str(exp.issue),
        "expected_catalog": str(exp.catalog),
        "item_catalog": "" if item_catalog is None else str(item_catalog),
        "month_ok": _yes_no(None if month is None else month == exp.month),
        "year_ok": _yes_no(None if year_from is None else year_from == exp.year),
        "issue_ok": _yes_no(None if issue is None else issue == exp.issue),
        "catalog_ident_ok": _yes_no(None if catalog is None else catalog == exp.catalog),
        "catalog_item_ok": _yes_no(None if item_catalog is None else item_catalog - 2 == exp.catalog),
    }
