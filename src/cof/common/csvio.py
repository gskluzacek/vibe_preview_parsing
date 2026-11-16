"""Small CSV helpers: read rows as dictionaries and write files atomically."""

import csv
import os
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries.

    Args:
        path: CSV file with a header row.

    Returns:
        One dictionary per data row; an empty list if the file is missing.
    """
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows_atomic(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    """Write a CSV file by writing a temporary file and renaming it.

    A crash while writing therefore cannot truncate an existing file.

    Args:
        path: Destination file; parent directories are created.
        fieldnames: Column names, in order.
        rows: Row dictionaries; keys must be in ``fieldnames``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)
