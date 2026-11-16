"""Stage 1b: read the site's COF listing page as it looked at several dates.

The page linked the forms available at the time, so its links are a second list of what existed, apart
from guessing addresses.
"""

from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from cof.acquire.params import AcquireParams
from cof.acquire.urls import classify
from cof.acquire.wayback import WaybackClient
from cof.common.csvio import write_rows_atomic
from cof.common.months import month_index

LINK_COLUMNS = ("capture", "month", "kind", "href")


class _HrefCollector(HTMLParser):
    """Collects the ``href`` of every ``<a>`` tag."""

    def __init__(self) -> None:
        """Start with no links."""
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the target of a link."""
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value)


def cof_links(html: str) -> list[dict[str, str]]:
    """Extract COF links from a listing page.

    Args:
        html: Page source.

    Returns:
        Rows with ``month``, ``kind`` and ``href``, ordered by month then kind, without duplicates.
    """
    parser = _HrefCollector()
    parser.feed(html)
    found = {(classify(href), href) for href in parser.hrefs}
    keyed = sorted(
        ((cof, href) for cof, href in found if cof is not None),
        key=lambda item: (month_index(item[0].month), item[0].kind),
    )
    return [{"month": cof.month, "kind": cof.kind, "href": href} for cof, href in keyed]


def sample_captures(rows: list[list[str]], header: list[str], every_days: int) -> list[tuple[str, str]]:
    """Pick roughly one usable capture of the listing page per ``every_days``.

    Args:
        rows: Index rows.
        header: Column names of ``rows``.
        every_days: Minimum number of days between chosen captures.

    Returns:
        ``(timestamp, original)`` pairs, oldest first.
    """
    ix = {name: i for i, name in enumerate(header)}
    usable = sorted(
        (row[ix["timestamp"]], row[ix["original"]])
        for row in rows
        if row[ix["statuscode"]] == "200" and row[ix["mimetype"]] == "text/html"
    )
    chosen: list[tuple[str, str]] = []
    last: datetime | None = None
    for timestamp, original in usable:
        day = datetime.strptime(timestamp[:8], "%Y%m%d")
        if last is None or (day - last).days >= every_days:
            chosen.append((timestamp, original))
            last = day
    return chosen


def fetch_listing(
    client: WaybackClient, params: AcquireParams, acquire_dir: Path, every_days: int
) -> list[tuple[str, int]]:
    """Download sampled listing-page captures, keep the HTML, and write the extracted links.

    Args:
        client: Archive client.
        params: Configuration (the listing URL and index fields).
        acquire_dir: Output directory; HTML goes to ``raw/listing/``, links to ``listing_links.csv``.
        every_days: Sampling interval in days.

    Returns:
        ``(capture_timestamp, link_count)`` for each sampled capture.
    """
    raw = acquire_dir / "raw" / "listing"
    raw.mkdir(parents=True, exist_ok=True)
    fields = ["timestamp", "original", "statuscode", "mimetype", "length", "digest"]
    header, rows = client.cdx(params.listing_url, fields, params.cdx_limit)
    out_rows: list[dict[str, object]] = []
    summary: list[tuple[str, int]] = []
    for timestamp, original in sample_captures(rows, header, every_days):
        path = raw / f"{timestamp}.html"
        if not path.exists():  # captures never change, so a cached copy is final
            path.write_bytes(client.fetch_capture(timestamp, original))
        links = cof_links(path.read_bytes().decode("utf-8", "replace"))
        out_rows.extend({"capture": timestamp, **link} for link in links)
        summary.append((timestamp, len(links)))
    write_rows_atomic(acquire_dir / "listing_links.csv", LINK_COLUMNS, out_rows)
    return summary
