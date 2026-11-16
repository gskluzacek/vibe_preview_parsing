import gzip

import pytest

from cof.common.settings import Settings
from cof.normalize.normalize import NormalizationError, Patch, normalize_file
from cof.normalize.rules import load_rules

RULES = load_rules(Settings())
ITEM = "SS\tJAN13 0001\tBATMAN #1\t1/16/2013\tSRP:PI\t = $"
SOURCE = "\r\n".join(["PREVIEWS DECEMBER VOL. 23 #1", "", "PAGE 1\t", "HEAD", ITEM, "GE 24", "9"]) + "\r\n"


def test_normalizes_and_accounts_for_every_issue() -> None:
    done = normalize_file("JAN13", SOURCE.encode("cp1252"), RULES)
    assert done.status == "ok" and done.period == "2013_01"
    assert done.text is not None and "\r" not in done.text and done.text.endswith("9\n")
    assert done.source_lines == done.output_lines == 7
    statuses = {(r.rule_id, r.status) for r in done.records}
    assert {
        ("F07", "fixed"),
        ("L01", "fixed"),
        ("I01", "fixed"),
        ("I11", "fixed"),
        ("I09", "fixed"),
    } <= statuses
    assert ("L02", "open") in statuses  # the damaged PAGE line is reported, not changed
    assert "GE 24" in done.text


def test_second_pass_changes_nothing() -> None:
    first = normalize_file("JAN13", SOURCE.encode("cp1252"), RULES)
    assert first.text is not None
    second = normalize_file("JAN13", first.text.encode("utf-8"), RULES)
    assert second.text == first.text
    assert all(r.status in ("open", "info") for r in second.records)


@pytest.mark.parametrize(
    "encode",
    [lambda t: t.encode("cp1252"), lambda t: t.encode("utf-16"), lambda t: gzip.compress(t.encode("cp1252"))],
)
def test_every_source_encoding_gives_the_same_output(encode) -> None:  # type: ignore[no-untyped-def]
    text = SOURCE.replace("BATMAN", "POKÉMON")
    assert (
        normalize_file("JAN13", encode(text), RULES).text
        == normalize_file("JAN13", text.encode("utf-8"), RULES).text
    )


def test_facts_about_the_source_are_recorded() -> None:
    done = normalize_file("JAN13", gzip.compress(SOURCE.replace("BATMAN", "POKÉMON").encode("cp1252")), RULES)
    assert (done.encoding, done.compression, done.eol) == ("cp1252", "gzip", "crlf")
    assert done.non_ascii_bytes == 1


def test_foreign_layout_is_rejected() -> None:
    header = "PreviewsVolumeNo\tPreviewsNo\tOrderFormItemNo\tOrderFormItemDesc\tCountryCode\r\n"
    header += "33\t10\tOCT230001\tX\t002\r\n"
    done = normalize_file("NOV23", header.encode(), RULES)
    assert done.status == "rejected" and done.text is None


def test_patch_fixes_an_open_issue_and_is_reported_as_patched() -> None:
    patch = Patch(month="JAN13", line=6, old="GE 24", new="PAGE 24", reason="restore truncated PAGE line")
    done = normalize_file("JAN13", SOURCE.encode("cp1252"), RULES, [patch])
    assert done.text is not None and "PAGE 24" in done.text
    assert ("L02", "patched") in {(r.rule_id, r.status) for r in done.records}


def test_stale_patch_fails_loudly() -> None:
    patch = Patch(month="JAN13", line=6, old="something else", new="x", reason="stale")
    with pytest.raises(NormalizationError, match="stale"):
        normalize_file("JAN13", SOURCE.encode("cp1252"), RULES, [patch])


def test_patch_for_another_month_is_ignored() -> None:
    patch = Patch(month="FEB13", line=6, old="never matches", new="x", reason="other month")
    assert normalize_file("JAN13", SOURCE.encode("cp1252"), RULES, [patch]).status == "ok"
