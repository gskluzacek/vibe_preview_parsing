"""Stage 1a: query the archive's capture index and keep the raw answers."""

import json
from datetime import UTC, datetime
from pathlib import Path

from cof.acquire.params import AcquireParams
from cof.acquire.wayback import WaybackClient


def raw_cdx_dir(acquire_dir: Path) -> Path:
    """Return the directory that holds raw index responses."""
    return acquire_dir / "raw" / "cdx"


def fetch_index(client: WaybackClient, params: AcquireParams, acquire_dir: Path) -> dict[str, int]:
    """Query every configured URL pattern and store each answer unmodified.

    Args:
        client: Archive client.
        params: Configuration holding the URL patterns and index settings.
        acquire_dir: Output directory; files go to ``raw/cdx/<name>.json``.

    Returns:
        Number of captures returned per pattern name.
    """
    out = raw_cdx_dir(acquire_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, pattern in params.patterns.items():
        header, rows = client.cdx(pattern, params.cdx_fields, params.cdx_limit)
        record = {
            "pattern": pattern,
            "fetched_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "header": header,
            "rows": rows,
        }
        (out / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")
        counts[name] = len(rows)
    return counts
