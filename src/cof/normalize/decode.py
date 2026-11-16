r"""Decode a downloaded COF file to text, and record facts about how it was encoded.

Decoding to Unicode and splitting into lines (dropping the ``\\r`` of CRLF) is the *standard transform*:
it is applied to every file and is not reported as an edit. The facts it discovers are returned in
:class:`Decoded` so that unusual cases (mixed line endings, bare ``\\r``, bytes with no meaning in
Windows-1252) can be reported as real issues.
"""

import gzip
import zlib
from dataclasses import dataclass, field

# Bytes that Windows-1252 leaves undefined. They are replaced with U+FFFD and reported.
_CP1252_UNDEFINED = frozenset({0x81, 0x8D, 0x8F, 0x90, 0x9D})


@dataclass(frozen=True)
class Decoded:
    """A decoded file and the facts found while decoding it."""

    lines: list[str]  # text lines without line terminators
    encoding: str  # "ascii", "utf-8", "utf-8-bom", "utf-16" or "cp1252"
    eol: str  # "crlf", "lf", "mixed" or "none" (no line break at all)
    non_ascii_bytes: int  # number of bytes >= 0x80 in the source
    final_newline: bool  # whether the source ended with a line break
    compression: str = "none"  # "none", "gzip" or "gzip-truncated" (the archive stored the file compressed)
    bare_cr_lines: list[int] = field(default_factory=list)  # 1-based lines with a stray \r inside
    undefined_byte_lines: list[int] = field(default_factory=list)  # 1-based lines with cp1252-undefined bytes

    @property
    def text(self) -> str:
        """The whole file as text with LF line endings (and a final LF if the source had a line break)."""
        body = "\n".join(self.lines)
        return body + "\n" if self.final_newline else body


def _gunzip(data: bytes) -> tuple[bytes, str]:
    """Undo gzip compression if the bytes are a gzip stream.

    Some archive captures hold the file still compressed, with no header saying so, so the bytes arrive
    as a gzip stream. A stream cut short is decompressed as far as possible.

    Args:
        data: Raw bytes.

    Returns:
        ``(bytes, compression)`` where compression is ``"none"``, ``"gzip"`` or ``"gzip-truncated"``.
    """
    if data[:2] != b"\x1f\x8b":
        return data, "none"
    try:
        return gzip.decompress(data), "gzip"
    except (OSError, EOFError, zlib.error):
        partial = zlib.decompressobj(wbits=31).decompress(data)  # keep whatever could be recovered
        return partial, "gzip-truncated"


def _decode_text(data: bytes) -> tuple[str, str, list[int]]:
    """Decode bytes, preferring strict UTF-8 and falling back to Windows-1252.

    Args:
        data: Raw file bytes.

    Returns:
        ``(text, encoding_name, offsets_of_undefined_bytes)``.
    """
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):  # UTF-16 byte-order mark (the codec removes it)
        return data.decode("utf-16"), "utf-16", []
    if data[:3] == b"\xef\xbb\xbf":
        return data.decode("utf-8-sig"), "utf-8-bom", []
    if not any(b >= 0x80 for b in data):
        return data.decode("ascii"), "ascii", []
    try:
        return data.decode("utf-8"), "utf-8", []
    except UnicodeDecodeError:
        pass  # not UTF-8: the published files are Windows-1252
    offsets = [i for i, b in enumerate(data) if b in _CP1252_UNDEFINED]
    if offsets:
        # Replace each undefined byte by '?' before decoding so the strict codec accepts the rest,
        # then swap in U+FFFD so the loss is visible in the text.
        buffer = bytearray(data)
        for i in offsets:
            buffer[i] = ord("?")
        text = buffer.decode("cp1252")
        chars = list(text)
        for i in offsets:  # cp1252 is one byte per character, so offsets still line up
            chars[i] = "�"
        return "".join(chars), "cp1252", offsets
    return data.decode("cp1252"), "cp1252", []


def decode_bytes(data: bytes) -> Decoded:
    """Decode a COF file.

    Args:
        data: Raw file bytes as downloaded.

    Returns:
        The decoded lines (LF-split) and the facts discovered while decoding.
    """
    data, compression = _gunzip(data)
    text, encoding, undefined = _decode_text(data)
    # Work on the decoded text; "\r\n" survives decoding unchanged in every supported encoding.
    raw_lines = text.split("\n") if text else []
    final_newline = text.endswith("\n")
    if final_newline:
        raw_lines.pop()  # the empty piece after the last line break is not a line
    crlf = sum(1 for line in raw_lines[: len(raw_lines) if final_newline else -1] if line.endswith("\r"))
    breaks = len(raw_lines) - (0 if final_newline else 1)
    if breaks <= 0:
        eol = "none"
    elif crlf == breaks:
        eol = "crlf"
    elif crlf == 0:
        eol = "lf"
    else:
        eol = "mixed"
    lines: list[str] = []
    bare_cr: list[int] = []
    for number, line in enumerate(raw_lines, start=1):
        if line.endswith("\r"):
            line = line[:-1]
        if "\r" in line:
            bare_cr.append(number)
        lines.append(line)
    undefined_lines: list[int] = []
    if undefined:
        # Map byte offsets to line numbers using the source bytes.
        starts = [0]
        starts += [i + 1 for i, b in enumerate(data) if b == 0x0A]
        for offset in undefined:
            number = sum(1 for s in starts if s <= offset)
            if number not in undefined_lines:
                undefined_lines.append(number)
    return Decoded(
        lines=lines,
        encoding=encoding,
        eol=eol,
        non_ascii_bytes=sum(1 for b in data if b >= 0x80),
        final_newline=final_newline,
        compression=compression,
        bare_cr_lines=bare_cr,
        undefined_byte_lines=undefined_lines,
    )
