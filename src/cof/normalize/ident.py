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
