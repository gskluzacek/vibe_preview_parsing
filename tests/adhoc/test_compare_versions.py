from pathlib import Path

from compare_versions import classify_pair, compare_versions, diff_lines

ITEM = "SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t"


def test_ident_line_correction() -> None:
    kind, detail = classify_pair("PREVIEWS DECEMBER VOL. 23 #1", "PREVIEWS JANUARY VOL. 23 #1")
    assert kind == "ident_line"
    assert (
        detail
        == "identification line corrected from: PREVIEWS DECEMBER VOL. 23 #1 to PREVIEWS JANUARY VOL. 23 #1"
    )


def test_whitespace_only() -> None:
    assert classify_pair("HEADING", "HEADING\t\t")[0] == "whitespace"


def test_item_field_change_is_named() -> None:
    assert classify_pair(ITEM, ITEM.replace("BATMAN", "SUPERMAN"))[0] == "item_sol_text"
    assert classify_pair(ITEM, ITEM.replace("$2.99", "$3.99"))[0] == "item_price"


def test_tab_count_change() -> None:
    kind, detail = classify_pair(ITEM, ITEM.replace("01/16/13\tSRP", "01/16/13\t\tSRP"))
    assert kind == "tab_count"
    assert detail == "corrected number of tabs between date and price"


def test_diff_lines_added_removed_replaced() -> None:
    old = ["a", "b", "c"]
    new = ["a", "B", "c", "d"]
    got = [(d.change_type, d.old_line_no, d.new_line_no) for d in diff_lines(old, new)]
    assert got == [("text_line", 2, 2), ("line_added", None, 4)]
    assert [d.change_type for d in diff_lines(["x", "y"], ["x"])] == ["line_removed"]
    assert diff_lines(old, old) == []


def test_gzip_and_plain_copies_of_the_same_file_have_no_content_difference(tmp_path: Path) -> None:
    import gzip

    from cof.common.csvio import write_rows_atomic

    body = b"PAGE 1\r\nSS\tJAN24 0001\tBATMAN #1\t01/16/24\tSRP: $2.99\t = $\t\r\n"
    for name, data in (("a.txt", gzip.compress(body)), ("b.txt", body)):
        (tmp_path / name).write_bytes(data)
    cols = ["month", "kind", "digest_ok", "timestamp", "digest", "path"]
    write_rows_atomic(
        tmp_path / "downloads.csv",
        cols,
        [
            {
                "month": "JAN24",
                "kind": "txt",
                "digest_ok": "1",
                "timestamp": "2024",
                "digest": "A",
                "path": "a.txt",
            },
            {
                "month": "JAN24",
                "kind": "txt",
                "digest_ok": "1",
                "timestamp": "2025",
                "digest": "B",
                "path": "b.txt",
            },
        ],
    )
    rows = compare_versions(tmp_path)
    assert [r["change_type"] for r in rows] == ["no_content_difference"]
    assert "gzip" in str(rows[0]["detail"])
