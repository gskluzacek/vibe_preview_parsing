import pytest

from cof.acquire.urls import CofUrl, classify


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "http://www.previewsworld.com/support/previews_docs/orderforms/MAR13_COF.txt",
            CofUrl("MAR13", "txt", 1),
        ),
        (
            "http://www.previewsworld.com/support/previews_docs/orderforms/archive/2013/JAN13_COF.pdf",
            CofUrl("JAN13", "pdf", 2),
        ),
        (
            "http://www.previewsworld.com/support/previews_docs/orderforms/archive/2009/JAN09/JAN09_COF.txt",
            CofUrl("JAN09", "txt", 2),
        ),
        ("https://www.previewsworld.com/Catalog/CustomerOrderForm/TXT/jul23", CofUrl("JUL23", "txt", 3)),
        ("https://previewsworld.com/Catalog/CustomerOrderForm/PDF/JAN18?x=1", CofUrl("JAN18", "pdf", 3)),
        (
            "http://previewsworld.com:80/support/previews_docs/orderforms/JAN13_COF.txt",
            CofUrl("JAN13", "txt", 1),
        ),
    ],
)
def test_classify_accepts(url: str, expected: CofUrl) -> None:
    assert classify(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://www.previewsworld.com/support/previews_docs/orderforms/archive/2009/APR09/",
        "https://www.previewsworld.com/Catalog/CustomerOrderForm/PDF/%CE%9C%CE%91%CE%A521",
        "https://www.previewsworld.com/Catalog/CustomerOrderForm/TXT/",
        "https://example.com/MAR13_COF.txt",
        "https://previewsworld.com/Catalog/CustomerOrderForm/TXT/XXX13",
    ],
)
def test_classify_rejects(url: str) -> None:
    assert classify(url) is None
