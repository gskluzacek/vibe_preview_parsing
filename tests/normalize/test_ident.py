import pytest

from cof.normalize.ident import corrected_line, expected_for, month_mismatch, number_mismatch, parse_ident


def test_expected_values_from_file_name() -> None:
    exp = expected_for("JAN13")
    assert (exp.month, exp.year, exp.volume, exp.issue) == (0, 2013, 23, 1)
    assert expected_for("JUN19").catalog == 369  # (29 - 1) * 12 + 6 + 27
    assert expected_for("MAR20").catalog == 378


@pytest.mark.parametrize(
    ("line", "variant"),
    [
        ("PREVIEWS JANUARY VOL. 23 #1", "A"),
        ("PREVIEWS JUNE V20 #6", "B"),
        ("NOV V19 #11", "B"),
        ("PREVIEWS JUNE 2019", "D1"),
        ("ISSUE #369 (VOL. 29 #6)", "D2"),
    ],
)
def test_parse_variants(line: str, variant: str) -> None:
    parts = parse_ident(line + "\t ")
    assert parts is not None and parts.variant == variant


def test_parse_rejects_other_lines() -> None:
    assert parse_ident("PREVIEWS PUBLICATIONS") is None


@pytest.mark.parametrize(
    ("line", "month", "fixed"),
    [
        ("PREVIEWS DECEMBER VOL. 23 #1", "JAN13", "PREVIEWS JANUARY VOL. 23 #1"),
        ("PREVIEWS JANUARY VOL. 22 #2", "FEB13", "PREVIEWS FEBRUARY VOL. 23 #2"),
        ("PREVIEWS JUL V20 #8", "AUG10", "PREVIEWS AUG V20 #8"),  # 3-letter style stays 3 letters
        ("NOV V19 #11", "DEC09", "DEC V19 #12"),
        ("PREVIEWS JUNE 2018", "JUN19", "PREVIEWS JUNE 2019"),
        ("ISSUE #999 (VOL. 29 #6)", "JUN19", "ISSUE #369 (VOL. 29 #6)"),
    ],
)
def test_corrected_line_keeps_the_published_style(line: str, month: str, fixed: str) -> None:
    parts = parse_ident(line)
    assert parts is not None
    exp = expected_for(month)
    assert (month_mismatch(parts, exp) or number_mismatch(parts, exp)) is not None
    assert corrected_line(parts, exp) == fixed


def test_consistent_line_has_no_mismatch() -> None:
    parts = parse_ident("PREVIEWS JAN V23 #1")
    assert parts is not None
    exp = expected_for("JAN13")
    assert month_mismatch(parts, exp) is None and number_mismatch(parts, exp) is None
