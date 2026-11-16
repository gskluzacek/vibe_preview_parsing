"""Classify the lines of a COF text file (spec section 3.1)."""

import re
from enum import StrEnum

PAGE_RE = re.compile(r"^PAGE (?:M-)?\d+$")
SOL_RE = re.compile(r"^[A-Z]{3}\d\d \d{4}$")
# Identification ("ident") line variants A-D (spec section 2.1).
IDENT_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^PREVIEWS [A-Z]+ VOL\. \d+ #\d+$"),  # A: month spelled out (or 3 letters)
    re.compile(r"^PREVIEWS [A-Z]+ V\d+ #\d+$"),  # B: month spelled out or 3 letters
    re.compile(r"^PREVIEWS ORDER FORM$"),  # C, line 1
    re.compile(r"^[A-Z]+ V\d+ #\d+$"),  # C, line 2
    re.compile(r"^PREVIEWS [A-Z]+ \d{4}$"),  # D, line 1
    re.compile(r"^ISSUE #\d+ \(VOL\. \d+ #\d+\)$"),  # D, line 2
)
_MAX_IDENT_SEARCH = 8  # with no PAGE line at all, look for an ident in this many first lines


class LineType(StrEnum):
    """The kind of a line in a COF text file."""

    BLANK = "BLANK"
    PAGE = "PAGE"
    NOTE = "NOTE"
    IDENT = "IDENT"
    ITEM = "ITEM"
    FOOTER = "FOOTER"
    ANNOTATION = "ANNOTATION"
    HEADING = "HEADING"
    UNKNOWN = "UNKNOWN"


def is_item_line(line: str) -> bool:
    """Tell whether a line is an item line.

    The predicate is "column 1 is not empty" (spec 3.2), which also catches items with a malformed sol
    code; "at least two tabs" would wrongly accept tab-padded headings.

    Args:
        line: One line without its terminator.

    Returns:
        True if the line has a non-empty second tab-separated field.
    """
    fields = line.split("\t")
    return len(fields) >= 2 and fields[1].strip() != ""


def classify_lines(lines: list[str]) -> list[LineType]:
    """Assign a type to every line (first matching rule wins).

    Args:
        lines: File lines without terminators.

    Returns:
        One :class:`LineType` per line, in order.
    """
    stripped = [line.strip(" \t") for line in lines]
    first_page = next((i for i, s in enumerate(stripped) if PAGE_RE.match(s)), None)
    ident_end = first_page if first_page is not None else _MAX_IDENT_SEARCH
    last_nonblank = max((i for i, s in enumerate(stripped) if s), default=-1)
    types: list[LineType] = []
    for i, (line, s) in enumerate(zip(lines, stripped, strict=True)):
        if not s:
            types.append(LineType.BLANK)
        elif PAGE_RE.match(s):
            types.append(LineType.PAGE)
        elif s.startswith("(NOTE:"):
            types.append(LineType.NOTE)
        elif i < ident_end and any(p.match(s) for p in IDENT_RES):
            types.append(LineType.IDENT)
        elif is_item_line(line):
            types.append(LineType.ITEM)
        elif i == last_nonblank and s.isdigit():
            types.append(LineType.FOOTER)
        elif s.startswith("[") and s.endswith("]"):
            types.append(LineType.ANNOTATION)
        elif "\t" not in s and any(c.isalpha() for c in s):
            types.append(LineType.HEADING)
        else:
            types.append(LineType.UNKNOWN)
    return types
