from pathlib import Path

from cof.normalize.items import KNOWN_FLAGS
from flag_inventory import DOC, inventory

HEADER = "\t".join(
    ["src_line", "page", "section", "merchandise_flag", "kind", "flag", "sol_code", "text"]
    + ["release_date", "price_designation", "price"]
)


def test_inventory_counts_item_rows_only(tmp_path: Path) -> None:
    rows = ["1\t0\t1\t0\tD\t\t\tIDENT\t\t\t", "2\t1\t1\t0\tI\tSS\t2013-01-0001-0\tA\t\tSRP\t1.00",
            "3\t1\t1\t0\tI\tS\t2013-01-0002-0\tB\t\tSRP\t1.00", "4\t1\t1\t0\tH\tSS\t\tC\t\t\t"]  # fmt: skip
    (tmp_path / "2013_01.txt").write_text("\n".join([HEADER, *rows]) + "\n")
    table = inventory(tmp_path)
    assert "| `SS` | 1 | 2013_01 | 2013_01 | A | yes |" in table
    assert "| `S` | 1 |" in table and "no (rule I13)" in table


def test_every_known_flag_is_documented() -> None:
    text = DOC.read_text(encoding="utf-8")
    for flag in KNOWN_FLAGS - {""}:
        for part in flag.split():
            assert f"`{part}`" in text or f"| {part} " in text, part
