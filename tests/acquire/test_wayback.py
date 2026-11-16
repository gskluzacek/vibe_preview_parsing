import httpx
import pytest

from cof.acquire.wayback import WaybackClient, WaybackError, looks_offline

OFFLINE = b"<html><head><title>Internet Archive: Temporarily Offline</title></head></html>"


def make_client(handler: httpx.MockTransport, retries: int = 3) -> tuple[WaybackClient, list[float]]:
    sleeps: list[float] = []
    return WaybackClient(delay=1.0, retries=retries, transport=handler, sleep=sleeps.append), sleeps


def test_looks_offline() -> None:
    assert looks_offline(OFFLINE)
    assert not looks_offline(b"PREVIEWS JAN VOL 19")


def test_retries_past_the_offline_page() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, content=OFFLINE if len(calls) == 1 else b"data")

    client, sleeps = make_client(httpx.MockTransport(handler))
    assert client.get("https://web.archive.org/x") == b"data"
    assert len(calls) == 2
    assert sleeps[0] == 1.0  # pause before the first request
    assert max(sleeps) >= 1.0  # and a backoff pause between attempts


def test_gives_up_after_all_attempts() -> None:
    client, _ = make_client(httpx.MockTransport(lambda r: httpx.Response(503)), retries=3)
    with pytest.raises(WaybackError, match="3 attempts"):
        client.get("https://web.archive.org/x")


def test_does_not_retry_not_found() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404)

    client, _ = make_client(httpx.MockTransport(handler))
    with pytest.raises(WaybackError, match="404"):
        client.get("https://web.archive.org/x")
    assert len(calls) == 1


def test_cdx_parses_json_and_sends_query() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(
            200, json=[["timestamp", "original"], ["2013", "http://a"], ["2014", "http://b"]]
        )

    client, _ = make_client(httpx.MockTransport(handler))
    header, rows = client.cdx("example.com/*", ["timestamp", "original"], 50)
    assert header == ["timestamp", "original"]
    assert rows == [["2013", "http://a"], ["2014", "http://b"]]
    assert seen == {"url": "example.com/*", "output": "json", "fl": "timestamp,original", "limit": "50"}


def test_cdx_empty_answer() -> None:
    client, _ = make_client(httpx.MockTransport(lambda r: httpx.Response(200, content=b"")))
    assert client.cdx("nothing/*", ["timestamp"], 10) == (["timestamp"], [])


def test_fetch_capture_requests_unrewritten_content() -> None:
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, content=b"bytes")

    client, _ = make_client(httpx.MockTransport(handler))
    assert client.fetch_capture("20130116201840", "http://x/JAN13_COF.txt") == b"bytes"
    assert urls == ["https://web.archive.org/web/20130116201840id_/http://x/JAN13_COF.txt"]
