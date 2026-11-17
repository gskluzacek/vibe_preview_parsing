import pytest

from cof.normalize.context import Issue, build_context
from cof.normalize.rules import detect_all

A = "SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t"
IDENT = "PREVIEWS JANUARY VOL. 23 #1"


def run(
    text: str, month: str = "JAN13", encoding: str = "cp1252", newline: str = "\r\n"
) -> dict[str, list[Issue]]:
    """Detect issues in a small file and group them by rule id."""
    body = newline.join(text.split("\n")) + newline
    out: dict[str, list[Issue]] = {}
    for issue in detect_all(build_context(month, body.encode(encoding))):
        out.setdefault(issue.rule_id, []).append(issue)
    return out


def file_with(*item_lines: str, ident: str = IDENT) -> str:
    return "\n".join([ident, "", "PAGE 1", "HEADING", *item_lines, "", "9"])


def test_clean_file_has_no_issues() -> None:
    assert run(file_with(A)) == {}


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        (A[:-1], "I01"),  # 6 fields: no trailing empty field
        ("SS\tJAN13 0001\t\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", "I02"),  # extra empty field
        ("SS\tJAN13 0001\tBATMAN #1\tSRP: $2.99\t = $\t", "I03"),  # no date
        ("SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t ", "I04"),  # odd tail
        ("SS\tJAN138491\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", "I05"),
        ("SS\tJAN13 12\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", "I06"),
        ("SS\tFEB13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", "I07"),
        ("SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP:PI\t = $\t", "I09"),
        ("SS\tJAN13 0001\tBATMAN #1\t01/16/13\tFREE!\t = $\t", "I10"),
        ("SS\tJAN13 0001\tBATMAN #1\t1/16/2013\tSRP: $2.99\t = $\t", "I11"),
        ("SS\tJAN13 0001\tBATMAN #1\t13/45/13\tSRP: $2.99\t = $\t", "I12"),
        ("ZZ\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99\t = $\t", "I13"),
        ("SS\tJAN13 0001\t BATMAN #1 \t01/16/13\tSRP: $2.99\t = $\t", "I14"),
        ("SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $2.99 \t = $\t", "I19"),
        ('SS\tJAN13 0001\tBATMAN #1\t01/16/13\t"SRP: $1,100.00 "\t = $\t', "I20"),
        ("SS\tJAN13 0001\tBATMAN (#1\t01/16/13\tSRP: $2.99\t = $\t", "I17"),
        ("SS\tJAN13 0001\tBATMAN  #1\t01/16/13\tSRP: $2.99\t = $\t", "I18"),
        ("SS\tJAN13 0001\tBATMAN\t01/16/13", "I16"),
        ("\tJAN13 0001\tDO NOT ORDER FROM THIS LINE", "L06"),
    ],
)
def test_item_rules(line: str, rule: str) -> None:
    assert rule in run(file_with(line)), rule


def test_duplicate_sol_code_reported_on_second_occurrence() -> None:
    found = run(file_with(A, A))["I08"]
    assert [i.line for i in found] == [6]


def test_placeholder_with_three_fields_is_not_a_field_count_error() -> None:
    found = run(file_with("\tJAN13 0001\tDO NOT ORDER FROM THIS LINE"))
    assert "I16" not in found and "L06" in found


def test_replacement_character_is_flagged_everywhere() -> None:
    assert "I15" in run(file_with(A) + "\nPOK�MON", encoding="utf-8")


def test_ident_rules() -> None:
    assert "F06" in run("PAGE 1\nHEADING\n" + A + "\n9")  # none
    assert "F07" in run(file_with(A, ident="PREVIEWS DECEMBER VOL. 23 #1"))
    assert "F08" in run(file_with(A, ident="PREVIEWS JANUARY VOL. 22 #1"))
    assert "F08" in run(file_with(A, ident="PREVIEWS JANUARY VOL. 23 #6"))
    d = "PREVIEWS JANUARY 2013\nISSUE #999 (VOL. 23 #1)"
    assert "F08" in run(file_with(A, ident=d))  # catalog number formula
    assert "F07" not in run(file_with(A, ident="PREVIEWS JAN V23 #1"))  # 3-letter form is fine


def test_footer_and_line_rules() -> None:
    assert "F09" in run("\n".join([IDENT, "PAGE 1", A, "no number at end"]))
    got = run(
        "\n".join(
            [
                IDENT,
                "PAGE 1\t\t",
                "HEADING\t\t",
                "GE 24",
                "PAGE 2999",
                "(NOTE: X)",
                "[ANN]",
                "??",
                "300",
                A,
                "9",
            ]
        )
    )
    assert {"L01", "L02", "L03", "L04", "L05", "L07", "L08"} <= set(got)
    assert len(got["L01"]) == 2


def test_file_level_facts() -> None:
    mixed = build_context("JAN13", b"PAGE 1\r\nHEAD\nPAGE 2\r\n9\r\n")
    assert {i.rule_id for i in detect_all(mixed)} >= {"F02"}
    assert "F03" in {i.rule_id for i in detect_all(build_context("JAN13", b"PAGE 1\r\nA\rB\r\n9\r\n"))}
    assert "F04" in {i.rule_id for i in detect_all(build_context("JAN13", b"PAGE 1\r\nA\x81B\r\n9\r\n"))}
    assert "F10" in {i.rule_id for i in detect_all(build_context("JAN13", b""))}


def test_foreign_layout_suppresses_line_rules() -> None:
    header = "PreviewsVolumeNo\tPreviewsNo\tOrderFormItemNo\tOrderFormItemDesc\tCountryCode"
    got = run(header + "\n33\t10\tOCT230001\tPREVIEWS #423\t002", month="NOV23")
    assert set(got) <= {"F01", "F06", "F09"} and "F01" in got


def test_thousands_separator_price_is_a_known_form() -> None:
    line = "SS\tJAN13 0001\tBATMAN #1\t01/16/13\tSRP: $1,094.99\t = $\t"
    assert run(file_with(line)) == {}
    quoted = run(file_with('SS\tJAN13 0001\tBATMAN #1\t01/16/13\t"SRP: $1,100.00 "\t = $\t'))
    assert set(quoted) == {"I19", "I20"}  # quoted, with a trailing space inside; the price itself is fine
