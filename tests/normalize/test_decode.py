from cof.normalize.decode import decode_bytes


def test_ascii_crlf() -> None:
    d = decode_bytes(b"PAGE 1\r\nA\tB\r\n")
    assert (d.encoding, d.eol, d.lines, d.final_newline) == ("ascii", "crlf", ["PAGE 1", "A\tB"], True)
    assert d.text == "PAGE 1\nA\tB\n"


def test_cp1252_original_bytes() -> None:
    # 0xC9 = E acute, 0xB7 = middle dot, 0x97 = em dash in Windows-1252
    d = decode_bytes(b"POK\xc9MON\r\nCOMICS \xb7 NOVELS\r\nMAVERICK\x97MAD\r\n")
    assert d.encoding == "cp1252"
    assert d.lines == ["POKÉMON", "COMICS · NOVELS", "MAVERICK—MAD"]
    assert d.non_ascii_bytes == 3 and d.undefined_byte_lines == []


def test_valid_utf8_is_detected_not_assumed() -> None:
    d = decode_bytes("POKÉMON\n".encode())
    assert (d.encoding, d.eol) == ("utf-8", "lf")
    assert d.lines == ["POKÉMON"]


def test_undefined_cp1252_byte_is_reported_and_replaced() -> None:
    d = decode_bytes(b"ok\r\nbad\x81byte\r\n")
    assert d.encoding == "cp1252"
    assert d.undefined_byte_lines == [2]
    assert d.lines[1] == "bad�byte"


def test_mixed_line_endings_and_bare_cr() -> None:
    d = decode_bytes(b"a\r\nb\nc\rd\r\n")
    assert d.eol == "mixed"
    assert d.bare_cr_lines == [3]  # the stray \r inside the third line


def test_no_final_newline_and_empty() -> None:
    d = decode_bytes(b"a\r\nb")
    assert (d.eol, d.final_newline, d.lines) == ("crlf", False, ["a", "b"])
    assert decode_bytes(b"").lines == [] and decode_bytes(b"x").eol == "none"


def test_gzip_stream_is_decompressed_and_reported() -> None:
    import gzip

    d = decode_bytes(gzip.compress(b"PAGE 1\r\nPOK\xc9MON\r\n"))
    assert (d.compression, d.encoding, d.lines) == ("gzip", "cp1252", ["PAGE 1", "POKÉMON"])


def test_truncated_gzip_is_recovered_as_far_as_possible() -> None:
    import gzip

    blob = gzip.compress(b"line\r\n" * 5000)
    d = decode_bytes(blob[: len(blob) // 2])
    assert d.compression == "gzip-truncated" and 0 < len(d.lines) < 5000
