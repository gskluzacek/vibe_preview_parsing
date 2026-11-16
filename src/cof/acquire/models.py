"""Data records of the acquire stage."""

from dataclasses import asdict, dataclass

MANIFEST_COLUMNS: tuple[str, ...] = (
    "month", "kind", "era", "timestamp", "original", "status", "mime", "length", "digest", "plausible",
)  # fmt: skip


@dataclass(frozen=True)
class Capture:
    """One archived capture of a single COF file, as listed in ``manifest.csv``."""

    month: str  # e.g. "JAN13"
    kind: str  # "txt" or "pdf"
    era: int  # URL era 1-3
    timestamp: str  # capture time, YYYYMMDDhhmmss
    original: str  # the address that was captured
    status: str  # HTTP status the archive recorded
    mime: str  # MIME type the archive recorded
    length: int  # stored (compressed) size reported by the index, not the file size
    digest: str  # the archive's content fingerprint: equal digests mean identical bytes
    plausible: bool  # status 200, expected MIME type and a minimum size

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Capture":
        """Build a capture from a manifest CSV row.

        Args:
            row: A row read by ``csv.DictReader``.

        Returns:
            The capture with numeric and boolean fields converted.
        """
        return cls(
            month=row["month"], kind=row["kind"], era=int(row["era"]), timestamp=row["timestamp"],
            original=row["original"], status=row["status"], mime=row["mime"],
            length=int(row["length"]), digest=row["digest"], plausible=row["plausible"] == "1",
        )  # fmt: skip

    def to_row(self) -> dict[str, object]:
        """Convert to a manifest CSV row.

        Returns:
            Column name to value, with the plausibility flag as ``1`` or ``0``.
        """
        row: dict[str, object] = asdict(self)
        row["plausible"] = int(self.plausible)
        return row
