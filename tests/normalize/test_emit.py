import pytest

from cof.normalize.context import build_context
from cof.normalize.emit import COLUMNS, EmitError, SolCodes, collapse, emit, format_date, render, split_price
from cof.normalize.fixers import apply_fixes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("MSRP: $1,094.99", ("MSRP", "1094.99")),
        ("SRP: $0.5".replace("0.5", "0.50"), ("SRP", "0.50")),
        ("$45.00", ("", "45.00")),
        ("SRP: PI", ("SRP", "")),
        ("SRP: AR", ("SRP", "")),
        ("SRP: FREE", ("SRP", "0.00")),
        ("PI", ("", "")),
        ("garbage", ("", "garbage")),
    ],
)
def test_split_price(raw: str, expected: tuple[str, str]) -> None:
    assert split_price(raw) == expected


def test_sol_codes_get_a_sequence_for_duplicates() -> None:
    sols = SolCodes()
    assert sols.format("SEP24 0239") == "2024-09-0239-0"
    assert sols.format("SEP24 0239") == "2024-09-0239-1"
    assert sols.format("STAR1") == "STAR1"  # malformed: kept
    with pytest.raises(EmitError):
        for _ in range(11):
            sols.format("JAN13 0001")


def test_dates_and_whitespace() -> None:
    assert format_date("07/08/15") == "2015-07-08" and format_date("") == ""
    assert collapse("  A \t  B\rC  ") == "A B C"


SOURCE = [
    "PREVIEWS MAR V19 #3",
    "",
    "PAGE 5",
    "HEAD  ONE",
    "\tMAR15 0001\tBATMAN  #1\t05/06/15\tSRP: $3.99\t = $\t",
    "(NOTE: x)",
    "\tMAR15 0002\tDO NOT ORDER FROM THIS LINE",
    "PAGE 2",
    "PAGE M-1",
    "\tMAR15 0001\tREPEAT\t\tMSRP: $1,000.00\t = $\t",
    "7",
]


def build() -> tuple[list[str], str]:
    ctx = build_context("MAR15", "\n".join(SOURCE).encode())
    lines, _ = apply_fixes(ctx)
    out = emit(ctx, lines)
    return [r.kind for r in out.rows], render(COLUMNS, out.rows)


def test_rows_pages_sections_and_dispositions() -> None:
    ctx = build_context("MAR15", "\n".join(SOURCE).encode())
    lines, _ = apply_fixes(ctx)
    out = emit(ctx, lines)
    assert [r.kind for r in out.rows] == ["D", "H", "I", "I"]
    assert out.rows[0].src_line == 1 and out.rows[0].text.startswith("PREVIEWS MARCH 2015 ISSUE #318")
    heading, first, repeat = out.rows[1], out.rows[2], out.rows[3]
    assert (heading.page, heading.section, heading.text) == (5, 1, "HEAD ONE")
    assert (first.sol_code, first.text, first.price) == ("2015-03-0001-0", "BATMAN #1", "3.99")
    # page 5 -> 2 and 2 -> M-1 are two restarts, so the repeat is in section 3
    assert (repeat.page, repeat.section, repeat.merchandise_flag) == (1, 3, 1)
    assert repeat.sol_code == "2015-03-0001-1" and repeat.price == "1000.00"
    assert [(r.kind, r.src_line) for r in out.sidecar] == [("NOTE", 6), ("PLACEHOLDER", 7)]
    assert sum(out.ledger.values()) == len(SOURCE)
    assert out.ledger["PAGE", "dropped"] == 3 and out.ledger["IDENT", "replaced"] == 1


def test_a_file_without_ident_gets_one_at_line_zero() -> None:
    ctx = build_context("MAR15", b"PAGE 1\nHEAD\n")
    out = emit(ctx, apply_fixes(ctx)[0])
    assert out.rows[0].kind == "D" and out.rows[0].src_line == 0
