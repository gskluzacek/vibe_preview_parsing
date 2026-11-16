from cof.normalize.classify import LineType, classify_lines, is_item_line

ITEM = "SS\tJAN13 0001\tBATMAN #1 (JAN120001)\t01/16/13\tSRP: $2.99\t = $\t"


def types(*lines: str) -> list[str]:
    return [t.value for t in classify_lines(list(lines))]


def test_basic_line_types_in_order() -> None:
    got = types(
        "PREVIEWS JANUARY VOL. 23 #1", "", "PAGE 1", "PREVIEWS PUBLICATIONS", ITEM, "(NOTE: X)", "143"
    )
    assert got == ["IDENT", "BLANK", "PAGE", "HEADING", "ITEM", "NOTE", "FOOTER"]


def test_page_forms_and_padding() -> None:
    assert types("PAGE 12\t\t\t", "PAGE M-3", "PAGE 7 ") == ["PAGE", "PAGE", "PAGE"]
    assert types("80 PAGE GIANT", "BETTIE PAGE") == ["HEADING", "HEADING"]  # not PAGE lines


def test_tab_padded_heading_is_not_an_item() -> None:
    assert not is_item_line("PREVIEWS PUBLICATIONS\t\t\t\t\t")
    assert types("PAGE 1", "PREVIEWS PUBLICATIONS\t\t\t\t\t")[1] == "HEADING"


def test_ident_only_before_first_page() -> None:
    assert types("PREVIEWS ORDER FORM", "NOV V19 #11", "PAGE 1", "PREVIEWS JUNE 2019")[:2] == [
        "IDENT",
        "IDENT",
    ]
    assert types("PAGE 1", "PREVIEWS JUNE 2019")[1] == "HEADING"


def test_malformed_sol_code_is_still_an_item() -> None:
    assert is_item_line("\tFEB138491\tTEXT\t01/01/13\tSRP: $1.00\t = $\t")


def test_footer_only_for_last_non_blank_line() -> None:
    assert types("PAGE 1", "300", ITEM, "70", "", "") == [
        "PAGE",
        "UNKNOWN",
        "ITEM",
        "FOOTER",
        "BLANK",
        "BLANK",
    ]


def test_annotation_and_unknown() -> None:
    assert types("PAGE 1", "[GR: FREE COMIC BOOK DAY]", "??") == ["PAGE", "ANNOTATION", "UNKNOWN"]
    assert LineType.UNKNOWN.value == "UNKNOWN"


def test_ident_variant_b_with_spelled_month() -> None:
    assert types("PREVIEWS JUNE V20 #6", "", "PAGE 19")[0] == "IDENT"
    assert types("PREVIEWS ORDER FORM", "OCTOBER V19 #10", "PAGE 1")[:2] == ["IDENT", "IDENT"]
