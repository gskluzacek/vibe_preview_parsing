"""Classify COF URLs: which month, text or PDF, and which of the three URL eras.

Era 1: ``/support/previews_docs/orderforms/MMMYY_COF.txt``          (current-month location)
Era 2: ``/support/previews_docs/orderforms/archive/YYYY/[MMMYY/]MMMYY_COF.txt``
Era 3: ``/Catalog/CustomerOrderForm/TXT/MMMYY`` (and ``/PDF/MMMYY``)
"""

import re
from typing import NamedTuple
from urllib.parse import unquote, urlsplit

from cof.common.months import MONTHS

# A file name such as JAN13, JAN13_COF or JAN13_COF.txt (case-insensitive).
_ALTERNATION = "|".join(MONTHS)
_SEGMENT = re.compile(rf"({_ALTERNATION})(\d\d)(?:_COF)?(?:\.(txt|pdf))?", re.IGNORECASE)


class CofUrl(NamedTuple):
    """The meaning of one COF URL."""

    month: str  # e.g. "JAN13"
    kind: str  # "txt" or "pdf"
    era: int  # 1, 2 or 3


def classify(url: str) -> CofUrl | None:
    """Work out which COF file a URL points at.

    Args:
        url: Any URL, as recorded by the archive.

    Returns:
        The month, kind and era, or ``None`` when the URL is not a single COF file (a directory, an
        unrelated page, an error address).
    """
    path = unquote(urlsplit(url).path)
    low = path.lower()
    if low.endswith("/"):  # a folder, not a file
        return None
    if "/support/previews_docs/orderforms/" in low:
        era = 2 if "/archive/" in low else 1
    elif "/catalog/customerorderform/" in low:
        era = 3
    else:
        return None
    match = _SEGMENT.fullmatch(path.rsplit("/", 1)[-1])
    if not match:
        return None
    month = match.group(1).upper() + match.group(2)
    if match.group(3):
        kind = match.group(3).lower()
    elif "/txt/" in low:  # era 3 has no extension; the folder says which kind
        kind = "txt"
    elif "/pdf/" in low:
        kind = "pdf"
    else:
        return None
    return CofUrl(month, kind, era)
