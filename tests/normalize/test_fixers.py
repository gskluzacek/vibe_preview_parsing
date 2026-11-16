import pytest

from cof.normalize.classify import classify_lines
from cof.normalize.context import FileContext
from cof.normalize.decode import decode_bytes
from cof.normalize.fixers import Change, apply_fixes, fix_ident, fix_item

CLEAN = "SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t"


def fixed(line: str) -> tuple[str, list[str]]:
    changes: list[Change] = []
    return fix_item(7, line, changes), [c.rule_id for c in changes]


def test_clean_line_is_untouched() -> None:
    assert fixed(CLEAN) == (CLEAN, [])


@pytest.mark.parametrize(
    ("line", "rules"),
    [
        (CLEAN[:-1], ["I01"]),
        ("SS\tJAN13 0001\t\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", ["I02"]),
        ("SS\tJAN13 0001\tBATMAN #1\tSRP: $2.99\t = $\t", ["I03"]),
        (CLEAN + " ", ["I04"]),
        (CLEAN.replace("JAN13 0001", "JAN130001"), ["I05"]),
        (CLEAN.replace("SRP: $2.99", "SRP:PI"), ["I09"]),
        (CLEAN.replace("01/16/13", "1/16/2013"), ["I11"]),
        (CLEAN.replace("BATMAN #1", " BATMAN #1 "), ["I14"]),
        (CLEAN.replace("SRP: $2.99", "SRP: $2.99 "), ["I19"]),
        (CLEAN.replace("SRP: $2.99", '"SRP: $1,100.00 "'), ["I20", "I19"]),
    ],
)
def test_each_repair_restores_the_clean_form(line: str, rules: list[str]) -> None:
    result, got = fixed(line)
    assert got == rules
    assert result.split("\t")[:2] == ["SS", "JAN13 0001"] and result.endswith("\t = $\t")
    assert len(result.split("\t")) == 7


def test_exact_values_after_repair() -> None:
    assert fixed(CLEAN.replace("01/16/13", "1/6/2013"))[0].split("\t")[3] == "01/06/13"
    assert fixed(CLEAN.replace("SRP: $2.99", '"SRP: $1,100.00 "'))[0].split("\t")[4] == "SRP: $1,100.00"
    assert fixed(CLEAN.replace("BATMAN #1", '"BATMAN 12"" TALL"'))[0].split("\t")[2] == 'BATMAN 12" TALL'
    assert fixed(CLEAN.replace("JAN13 0001", "FEB138491"))[0].split("\t")[1] == "FEB13 8491"


def test_unknown_layout_and_placeholder_are_kept_as_published() -> None:
    placeholder = "\tJAN13 0001\tDO NOT ORDER FROM THIS LINE"
    odd = "SS\tJAN13 0001\tBATMAN"
    assert fixed(placeholder) == (placeholder, [])
    assert fixed(odd) == (odd, [])


def test_fix_ident_only_changes_wrong_lines() -> None:
    changes: list[Change] = []
    assert fix_ident(1, "PREVIEWS JANUARY VOL. 23 #1", "JAN13", changes) == "PREVIEWS JANUARY VOL. 23 #1"
    assert changes == []
    assert fix_ident(1, "PREVIEWS DECEMBER VOL. 22 #1", "JAN13", changes) == "PREVIEWS JANUARY VOL. 23 #1"
    assert sorted(c.rule_id for c in changes) == ["F07", "F08"]


def test_apply_fixes_preserves_line_count_and_trims_non_item_lines() -> None:
    lines = ["PREVIEWS DECEMBER VOL. 23 #1", "", "PAGE 1\t\t", "HEADING\t\t\t", CLEAN[:-1], "  \t", "9"]
    ctx = FileContext("JAN13", decode_bytes("\r\n".join(lines).encode()), classify_lines(lines))
    out, changes = apply_fixes(ctx)
    assert len(out) == len(lines)
    assert (
        out[0] == "PREVIEWS JANUARY VOL. 23 #1"
        and out[2] == "PAGE 1"
        and out[3] == "HEADING"
        and out[5] == ""
    )
    assert {c.rule_id for c in changes} == {"F07", "L01", "I01"}
