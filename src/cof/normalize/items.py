"""Item-line structure: layouts, canonical fields, and the value patterns of each field (spec section 4)."""

import re
from datetime import datetime

TAIL = " = $"
CANONICAL_FIELDS = 7  # flag, sol code, text, release date, price, tail, trailing empty field
KNOWN_FLAGS = frozenset(
    {
        "",
        "SS",
        "SPOT",
        "OA",
        "FI",
        "KIDS",
        "GEM",
        "OA SS",
        "OA FI",
        "SS KIDS",
        "OA SPOT",
        "OA KIDS",
        "SS SPOT",
        "SS FI",
        "BL",
        "FO",
    }
)
SOL_STRICT_RE = re.compile(r"^[A-Z]{3}\d\d \d{4}$")
SOL_NOSPACE_RE = re.compile(r"^[A-Z]{3}\d{6}$")
_MONEY = r"\$(?:\d{1,3}(?:,\d{3})+|\d+)\.\d\d"  # $12.99 or $1,094.99
_STATUS = "PI|AR|FREE"  # previews inquiry (no price yet), advance reorder, free
PRICE_RE = re.compile(rf"^(?:M?SRP: (?:{_MONEY}|{_STATUS})|{_MONEY}|{_STATUS})$")
PRICE_NOSPACE_RE = re.compile(rf"^M?SRP:(?:{_MONEY}|{_STATUS})$")
DATE_RE = re.compile(r"^(\d\d)/(\d\d)/(\d\d)$")
DATE_LONG_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def layout_of(fields: list[str]) -> str:
    """Name the layout of an item line from its tab-separated fields.

    Layouts (spec 4.2): ``A`` canonical 7 fields; ``B`` 6 fields, no trailing empty field; ``C`` 8 fields
    with an empty field after the sol code; ``D`` 6 fields with the release date missing; ``P`` a
    three-field "DO NOT ORDER FROM THIS LINE" placeholder the publisher left in; ``X`` anything else.

    Args:
        fields: The line split on tabs.

    Returns:
        ``"A"``, ``"B"``, ``"C"``, ``"D"``, ``"P"`` or ``"X"``.
    """
    n = len(fields)
    if n == 3 and fields[2].startswith("DO NOT ORDER FROM THIS LINE"):
        return "P"
    if n == 7:
        return "A"
    if n == 6 and fields[5] == TAIL:
        return "B"
    if n == 6 and fields[4] == TAIL and fields[5] == "":
        return "D"
    if n == 8 and fields[2] == "":
        return "C"
    return "X"


def canonical_fields(fields: list[str]) -> list[str] | None:
    """Rewrite an item line's fields into the canonical 7-field layout.

    Args:
        fields: The line split on tabs.

    Returns:
        Seven fields (flag, sol code, text, date, price, tail, empty), or ``None`` for an unknown layout.
    """
    layout = layout_of(fields)
    if layout == "A":
        return list(fields)
    if layout == "B":
        return [*fields, ""]
    if layout == "C":
        return [*fields[:2], *fields[3:]]
    if layout == "D":
        return [*fields[:3], "", *fields[3:]]
    return None


def parse_date(value: str) -> datetime | None:
    """Parse a release date in either known form.

    Args:
        value: Text of the date field.

    Returns:
        The date, or ``None`` if it is not a valid date in ``mm/dd/yy`` or ``m/d/yyyy`` form.
    """
    for pattern, fmt in ((DATE_RE, "%m/%d/%y"), (DATE_LONG_RE, "%m/%d/%Y")):
        if pattern.match(value):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                return None
    return None


def is_quoted(field: str) -> bool:
    """Tell whether a field is wrapped in CSV-style double quotes."""
    return len(field) >= 2 and field.startswith('"') and field.endswith('"')


def unquote(field: str) -> str:
    """Remove CSV-style quoting: the outer quotes, and ``""`` inside becomes ``"``.

    Args:
        field: A field, quoted or not.

    Returns:
        The field's real text.
    """
    return field[1:-1].replace('""', '"') if is_quoted(field) else field
