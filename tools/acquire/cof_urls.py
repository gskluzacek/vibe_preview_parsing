"""Classify a COF URL: which month, text or PDF, and which of the three URL eras.

Era 1: /support/previews_docs/orderforms/MMMYY_COF.txt          (current-month location)
Era 2: /support/previews_docs/orderforms/archive/YYYY/[MMMYY/]MMMYY_COF.txt
Era 3: /Catalog/CustomerOrderForm/TXT/MMMYY  (and /PDF/MMMYY)
"""
import re
from collections import namedtuple
from urllib.parse import unquote, urlsplit

MONTHS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')
_SEG = re.compile(r'(%s)(\d\d)(?:_COF)?(?:\.(txt|pdf))?' % '|'.join(MONTHS), re.I)

CofUrl = namedtuple('CofUrl', 'month kind era')


def month_index(month):
    """'JAN09' -> (9, 0), usable for ordering and ranges."""
    return (int(month[3:]), MONTHS.index(month[:3]))


def classify(url):
    """Return CofUrl(month, kind, era) or None when the URL is not a single COF file."""
    path = unquote(urlsplit(url).path)
    low = path.lower()
    if low.endswith('/'):
        return None
    if '/support/previews_docs/orderforms/' in low:
        era = 2 if '/archive/' in low else 1
    elif '/catalog/customerorderform/' in low:
        era = 3
    else:
        return None
    segment = path.rsplit('/', 1)[-1]
    m = _SEG.fullmatch(segment)
    if not m:
        return None
    month = m.group(1).upper() + m.group(2)
    if m.group(3):
        kind = m.group(3).lower()
    elif '/txt/' in low:
        kind = 'txt'
    elif '/pdf/' in low:
        kind = 'pdf'
    else:
        return None
    return CofUrl(month, kind, era)


def months_between(first, last):
    """Inclusive list of MMMYY strings from first to last."""
    (y0, m0), (y1, m1) = month_index(first), month_index(last)
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        out.append('%s%02d' % (MONTHS[m], y))
        m += 1
        if m == 12:
            y, m = y + 1, 0
    return out
