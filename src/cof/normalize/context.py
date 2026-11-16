"""The data a detector works on: one decoded, classified file, and the issues found in it."""

from dataclasses import dataclass

from cof.normalize.classify import LineType, classify_lines
from cof.normalize.decode import Decoded, decode_bytes


@dataclass(frozen=True)
class Issue:
    """One problem found in a file."""

    rule_id: str  # e.g. "I03"; see config/rules.yaml
    line: int | None  # 1-based line number, or None for a whole-file issue
    evidence: str  # short text showing what was found


@dataclass(frozen=True)
class FileContext:
    """A decoded and classified file, ready for the detectors."""

    month: str  # month code from the file name, e.g. "JAN13"
    decoded: Decoded
    types: list[LineType]

    @property
    def lines(self) -> list[str]:
        """The decoded lines, without terminators."""
        return self.decoded.lines

    def typed_lines(self, line_type: LineType) -> list[tuple[int, str]]:
        """List the lines of one type.

        Args:
            line_type: The type to select.

        Returns:
            ``(1-based line number, text)`` pairs in file order.
        """
        return [
            (i + 1, text)
            for i, (text, t) in enumerate(zip(self.lines, self.types, strict=True))
            if t == line_type
        ]


def build_context(month: str, data: bytes) -> FileContext:
    """Decode and classify a file.

    Args:
        month: Month code of the file, taken from the source file name (the authoritative period).
        data: Raw file bytes as downloaded.

    Returns:
        The context for the detectors.
    """
    decoded = decode_bytes(data)
    return FileContext(month=month, decoded=decoded, types=classify_lines(decoded.lines))
