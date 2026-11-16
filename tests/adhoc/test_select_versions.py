import gzip
from pathlib import Path

from cof.common.csvio import write_rows_atomic
from cof.common.settings import Settings
from select_versions import select_all

ITEM = "SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t"


def cof(ident: str, extra: str = "") -> bytes:
    lines = [ident, "", "PAGE 1", "HEADING", ITEM, *([extra] if extra else []), "", "9"]
    return ("\r\n".join(lines) + "\r\n").encode("cp1252")


def setup(tmp_path: Path, files: list[tuple[str, str, str, bytes, str]]) -> Path:
    """Write files and a downloads.csv; each entry is (month, kind, timestamp, data, content_ok)."""
    rows = []
    for i, (month, kind, ts, data, content_ok) in enumerate(files):
        path = f"{kind}/{month}/d{i}_{ts}.{kind}"
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(data)
        rows.append(
            {"month": month, "kind": kind, "digest": f"D{i}", "timestamp": ts, "path": path,
             "digest_ok": "1", "content_ok": content_ok}
        )  # fmt: skip
    write_rows_atomic(tmp_path / "downloads.csv", list(rows[0]), rows)
    return tmp_path


def by_digest(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(r["digest"]): r for r in rows}


def test_single_version_is_only_version(tmp_path: Path) -> None:
    rows = select_all(
        setup(tmp_path, [("JAN13", "txt", "2013", cof("PREVIEWS JANUARY VOL. 23 #1"), "1")]), Settings()
    )
    assert [r["status"] for r in rows] == ["only_version"]


def test_corrected_ident_version_is_selected_and_reason_is_recorded(tmp_path: Path) -> None:
    wrong, right = cof("PREVIEWS DECEMBER VOL. 23 #1"), cof("PREVIEWS JANUARY VOL. 23 #1")
    rows = by_digest(
        select_all(
            setup(tmp_path, [("JAN13", "txt", "2012", wrong, "1"), ("JAN13", "txt", "2013", right, "1")]),
            Settings(),
        )
    )
    assert rows["D1"]["status"] == "selected"
    assert rows["D0"]["status"] == "not_used"
    assert str(rows["D0"]["reason_detail"]).startswith(
        "identification line corrected from: PREVIEWS DECEMBER VOL. 23 #1 to PREVIEWS JANUARY VOL. 23 #1"
    )


def test_later_version_with_wrong_ident_is_not_preferred(tmp_path: Path) -> None:
    right, wrong = cof("PREVIEWS JANUARY VOL. 23 #1"), cof("PREVIEWS DECEMBER VOL. 23 #1")
    rows = by_digest(
        select_all(
            setup(tmp_path, [("JAN13", "txt", "2012", right, "1"), ("JAN13", "txt", "2013", wrong, "1")]),
            Settings(),
        )
    )
    assert rows["D0"]["status"] == "selected" and rows["D1"]["status"] == "not_used"
    assert "differs" in str(rows["D1"]["reason_detail"])


def test_gzip_copy_of_the_same_content_is_not_used(tmp_path: Path) -> None:
    data = cof("PREVIEWS JANUARY VOL. 23 #1")
    rows = by_digest(
        select_all(
            setup(
                tmp_path,
                [("JAN13", "txt", "2013", gzip.compress(data), "1"), ("JAN13", "txt", "2014", data, "1")],
            ),
            Settings(),
        )
    )
    assert rows["D1"]["status"] == "selected"  # the plain copy is kept
    assert rows["D0"]["reason_code"] == "identical_content"


def test_more_complete_version_wins(tmp_path: Path) -> None:
    short, longer = (
        cof("PREVIEWS JANUARY VOL. 23 #1"),
        cof("PREVIEWS JANUARY VOL. 23 #1", ITEM.replace("0001", "0002")),
    )
    rows = by_digest(
        select_all(
            setup(tmp_path, [("JAN13", "txt", "2012", short, "1"), ("JAN13", "txt", "2013", longer, "1")]),
            Settings(),
        )
    )
    assert rows["D1"]["status"] == "selected" and "extra line" in str(rows["D0"]["reason_detail"])


def test_foreign_layout_is_never_selected(tmp_path: Path) -> None:
    foreign = b"PreviewsVolumeNo\tPreviewsNo\tOrderFormItemNo\tDesc\tCode\r\n33\t10\tOCT230001\tX\t002\r\n"
    good = cof("PREVIEWS JANUARY VOL. 23 #1")
    rows = by_digest(
        select_all(
            setup(tmp_path, [("JAN13", "txt", "2023", foreign, "1"), ("JAN13", "txt", "2024", good, "1")]),
            Settings(),
        )
    )
    assert rows["D0"]["reason_code"] == "foreign_layout" and rows["D1"]["status"] == "selected"


def test_pdf_truncated_is_not_used_and_latest_complete_is_selected(tmp_path: Path) -> None:
    pdfs = [
        ("JAN18", "pdf", "2021", b"%PDF-1.7 cut", "0"),
        ("JAN18", "pdf", "2022", b"%PDF-1.7 %%EOF", "1"),
        ("JAN18", "pdf", "2023", b"%PDF-1.7 %%EOF", "1"),
    ]
    rows = by_digest(select_all(setup(tmp_path, pdfs), Settings()))
    assert rows["D0"]["reason_detail"] == "PDF file was truncated (no %%EOF marker)"
    assert rows["D2"]["status"] == "selected" and rows["D1"]["reason_code"] == "superseded"
