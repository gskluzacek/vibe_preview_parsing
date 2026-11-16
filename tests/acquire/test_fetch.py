import base64
import hashlib
from pathlib import Path

import httpx

from cof.acquire.fetch import archive_digest, distinct_versions, looks_right, run_fetch, stored_path
from cof.acquire.models import Capture
from cof.acquire.wayback import WaybackClient
from cof.common.csvio import read_rows


def cap(
    month: str = "JAN13", kind: str = "txt", digest: str = "AAAA", ts: str = "2013", ok: bool = True
) -> Capture:
    return Capture(month, kind, 3, ts, f"http://x/{month}", "200", "text/plain", 100, digest, ok)


def test_archive_digest_is_base32_sha1() -> None:
    assert archive_digest(b"") == "3I42H3S6NNFQ2MSVX7XZKYAYSCX5QBYJ"


def test_looks_right() -> None:
    assert looks_right("pdf", b"%PDF-1.4 ... %%EOF\n")
    assert not looks_right("pdf", b"%PDF-1.4 truncated mid-stream")
    assert not looks_right("pdf", b"<html>")
    assert not looks_right("txt", b"  <!DOCTYPE html><html>")
    assert looks_right("txt", b"PREVIEWS JAN VOL 19")


def test_distinct_versions_takes_earliest_plausible_capture_per_digest() -> None:
    rows = [
        cap(digest="A", ts="2013"),
        cap(digest="A", ts="2012"),
        cap(digest="B", ts="2014"),
        cap(digest="C", ts="2011", ok=False),
        cap(month="FEB13", digest="D"),
    ]
    got = distinct_versions(rows, {"JAN13"}, {"txt"})
    assert sorted((c.digest, c.timestamp) for c in got) == [("A", "2012"), ("B", "2014")]


def _client(payloads: dict[str, bytes]) -> WaybackClient:
    def handler(request: httpx.Request) -> httpx.Response:
        for key, data in payloads.items():
            if key in str(request.url):
                return httpx.Response(200, content=data)
        return httpx.Response(404)

    return WaybackClient(delay=0, retries=2, transport=httpx.MockTransport(handler), sleep=lambda s: None)


def test_run_fetch_downloads_verifies_logs_and_skips_on_rerun(tmp_path: Path) -> None:
    data = b"PREVIEWS JANUARY VOL. 23 #1\r\n"
    good = Capture(
        "JAN13", "txt", 3, "2013", "http://x/JAN13", "200", "text/plain", 1, archive_digest(data), True
    )
    bad_digest = Capture("FEB13", "txt", 3, "2013", "http://x/FEB13", "200", "text/plain", 1, "WRONG", True)
    missing = Capture("MAR13", "txt", 3, "2013", "http://x/MAR13", "200", "text/plain", 1, "ZZZZ", True)
    client = _client({"JAN13": data, "FEB13": b"other"})
    lines: list[str] = []

    result = run_fetch(
        client,
        [good, bad_digest, missing],
        tmp_path,
        [("JAN13", "txt"), ("FEB13", "txt"), ("MAR13", "txt")],
        lines.append,
    )
    assert (result.fetched, len(result.failed)) == (2, 1)
    assert stored_path(tmp_path, good).read_bytes() == data  # stored exactly as fetched
    log = {r["month"]: r for r in read_rows(tmp_path / "downloads.csv")}
    assert log["JAN13"]["digest_ok"] == "1" and log["JAN13"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert log["FEB13"]["digest_ok"] == "0"  # kept and flagged, not dropped
    assert "MAR13" not in log

    again = run_fetch(client, [good], tmp_path, [("JAN13", "txt")], lines.append)
    assert (again.fetched, again.skipped) == (0, 1)


def test_run_fetch_dry_run_writes_nothing(tmp_path: Path) -> None:
    lines: list[str] = []
    run_fetch(None, [cap()], tmp_path, [("JAN13", "txt")], lines.append, dry_run=True)
    assert lines and lines[0].startswith("would")
    assert not (tmp_path / "downloads.csv").exists()


def test_existing_file_is_rechecked_for_completeness(tmp_path: Path) -> None:
    truncated = b"%PDF-1.7 cut off"
    c = Capture(
        "JAN18", "pdf", 3, "2021", "http://x", "200", "application/pdf", 1, archive_digest(truncated), True
    )
    run_fetch(_client({"x": truncated}), [c], tmp_path, [("JAN18", "pdf")], lambda s: None)
    rows = read_rows(tmp_path / "downloads.csv")
    assert rows[0]["digest_ok"] == "1" and rows[0]["content_ok"] == "0"  # valid digest, incomplete file
    base32 = base64.b32encode(hashlib.sha1(truncated).digest()).decode()
    assert rows[0]["digest"] == base32
