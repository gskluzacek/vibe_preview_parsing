from pathlib import Path

from cof.common.csvio import write_rows_atomic
from link_pdfs import has_eof_marker, link_pdfs

COLUMNS = ["month", "kind", "digest", "timestamp", "path", "status", "reason_code", "reason_detail"]


def row(month: str, kind: str, name: str, status: str) -> dict[str, str]:
    return {"month": month, "kind": kind, "digest": name, "timestamp": "1", "path": f"{kind}/{month}/{name}",
            "status": status, "reason_code": "", "reason_detail": ""}  # fmt: skip


def test_one_relative_link_per_month_for_the_selected_version(tmp_path: Path) -> None:
    orig = tmp_path / "originals"
    for month, name, body in (("JAN13", "a.pdf", b"x%%EOF\n"), ("JAN13", "b.pdf", b"x%%EOF\n"),
                              ("FEB13", "c.pdf", b"cut off")):  # fmt: skip
        (orig / "pdf" / month).mkdir(parents=True, exist_ok=True)
        (orig / "pdf" / month / name).write_bytes(body)
    rows = [
        row("JAN13", "pdf", "a.pdf", "not_used"),
        row("JAN13", "pdf", "b.pdf", "selected"),
        row("FEB13", "pdf", "c.pdf", "only_version"),
        row("JAN13", "txt", "t.txt", "selected"),
    ]
    write_rows_atomic(orig / "selection.csv", COLUMNS, rows)
    links = tmp_path / "pdf"
    (links / "2001_01.pdf").parent.mkdir()
    (links / "2001_01.pdf").symlink_to("nowhere.pdf")  # stale link
    (links / "notes.txt").write_text("keep")
    report = link_pdfs(orig, links)
    assert report.linked == ["2013_01", "2013_02"] and report.truncated == ["2013_02"]
    assert report.removed == ["2001_01"] and (links / "notes.txt").exists()
    link = links / "2013_01.pdf"
    assert link.is_symlink() and not Path(link.readlink()).is_absolute()
    assert link.resolve() == (orig / "pdf" / "JAN13" / "b.pdf").resolve()
    assert link_pdfs(orig, links).linked == report.linked  # running again is harmless


def test_eof_marker_is_looked_for_at_the_end(tmp_path: Path) -> None:
    ok, cut = tmp_path / "ok.pdf", tmp_path / "cut.pdf"
    ok.write_bytes(b"a" * 5000 + b"%%EOF")
    cut.write_bytes(b"%%EOF" + b"a" * 5000)
    assert has_eof_marker(ok) and not has_eof_marker(cut)
