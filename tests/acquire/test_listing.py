from pathlib import Path

import httpx

from cof.acquire.listing import cof_links, fetch_listing, sample_captures
from cof.acquire.params import AcquireParams
from cof.acquire.wayback import WaybackClient
from cof.common.csvio import read_rows

HTML = """
<a href="/Catalog/CustomerOrderForm/TXT/FEB13">t</a>
<a href="/Catalog/CustomerOrderForm/PDF/JAN13">p</a>
<a href="/Catalog/CustomerOrderForm/TXT/JAN13">t</a>
<a href="/Catalog/CustomerOrderForm/TXT/JAN13">duplicate</a>
<a href="/Home/About">other</a><a>no href</a>
"""


def test_cof_links_orders_and_deduplicates() -> None:
    links = cof_links(HTML)
    assert [(link["month"], link["kind"]) for link in links] == [
        ("JAN13", "pdf"),
        ("JAN13", "txt"),
        ("FEB13", "txt"),
    ]


def test_sample_captures_spaces_captures_and_skips_unusable_ones() -> None:
    header = ["timestamp", "original", "statuscode", "mimetype"]
    rows = [
        ["20200101000000", "u", "200", "text/html"],
        ["20200110000000", "u", "200", "text/html"],  # too close to the previous
        ["20200201000000", "u", "404", "text/html"],  # not usable
        ["20200401000000", "u", "200", "text/html"],
    ]
    assert [t for t, _ in sample_captures(rows, header, 90)] == ["20200101000000", "20200401000000"]


def test_fetch_listing_caches_html_and_writes_links(tmp_path: Path, params: AcquireParams) -> None:
    index = [
        ["timestamp", "original", "statuscode", "mimetype", "length", "digest"],
        ["20200101000000", "http://x/list", "200", "text/html", "10", "A"],
    ]
    page = b'<a href="/Catalog/CustomerOrderForm/TXT/JAN20">t</a>'

    def handler(request: httpx.Request) -> httpx.Response:
        if "cdx" in str(request.url):
            return httpx.Response(200, json=index)
        return httpx.Response(200, content=page)

    client = WaybackClient(delay=0, retries=1, transport=httpx.MockTransport(handler), sleep=lambda s: None)
    assert fetch_listing(client, params, tmp_path, 90) == [("20200101000000", 1)]
    assert (tmp_path / "raw" / "listing" / "20200101000000.html").read_bytes() == page
    rows = read_rows(tmp_path / "listing_links.csv")
    assert rows == [
        {
            "capture": "20200101000000",
            "month": "JAN20",
            "kind": "txt",
            "href": "/Catalog/CustomerOrderForm/TXT/JAN20",
        }
    ]
