"""Helpers for COF month codes (``JAN13``) and the sortable ``YYYY_MM`` file-naming form (``2013_01``)."""

import re

MONTHS: tuple[str, ...] = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
_ALTERNATION = "|".join(MONTHS)
_MONTH_CODE = re.compile(rf"({_ALTERNATION})(\d\d)")
_PERIOD = re.compile(r"(\d{4})_(\d\d)")


def month_index(month: str) -> tuple[int, int]:
    """Return a sortable key for a month code.

    Args:
        month: A month code such as ``"JAN09"``.

    Returns:
        ``(two_digit_year, zero_based_month)``, for example ``(9, 0)``.
    """
    return (int(month[3:]), MONTHS.index(month[:3]))


def months_between(first: str, last: str) -> list[str]:
    """List month codes from ``first`` to ``last`` inclusive.

    Args:
        first: First month code, for example ``"NOV09"``.
        last: Last month code, for example ``"FEB10"``.

    Returns:
        Month codes in order, for example ``["NOV09", "DEC09", "JAN10", "FEB10"]``.
    """
    (year, mon), end = month_index(first), month_index(last)
    out: list[str] = []
    while (year, mon) <= end:
        out.append(f"{MONTHS[mon]}{year:02d}")
        mon += 1
        if mon == 12:  # roll over to January of the next year
            year, mon = year + 1, 0
    return out


def to_period(month: str) -> str:
    """Convert a month code to the sortable ``YYYY_MM`` form.

    Two-digit years are taken as 20YY, which covers every published COF (2009 onwards).

    Args:
        month: A month code such as ``"JAN13"``.

    Returns:
        The period name, for example ``"2013_01"``.

    Raises:
        ValueError: If ``month`` is not a valid month code.
    """
    if not _MONTH_CODE.fullmatch(month):
        raise ValueError(f"not a month code: {month!r}")
    year, mon = month_index(month)
    return f"{2000 + year:04d}_{mon + 1:02d}"


def from_period(period: str) -> str:
    """Convert a ``YYYY_MM`` period name back to a month code.

    Args:
        period: A period name such as ``"2013_01"``.

    Returns:
        The month code, for example ``"JAN13"``.

    Raises:
        ValueError: If ``period`` is not valid or the year is outside 2000-2099.
    """
    match = _PERIOD.fullmatch(period)
    if not match or not 2000 <= int(match.group(1)) <= 2099 or not 1 <= int(match.group(2)) <= 12:
        raise ValueError(f"not a period name: {period!r}")
    return f"{MONTHS[int(match.group(2)) - 1]}{int(match.group(1)) - 2000:02d}"
