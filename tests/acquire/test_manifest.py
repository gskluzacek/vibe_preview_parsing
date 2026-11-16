import shutil
from pathlib import Path

import pytest

from cof.acquire.manifest import build_captures, coverage_report, read_manifest, write_manifest
from cof.acquire.params import AcquireParams


@pytest.fixture
def acquire_dir(tmp_path: Path, fixtures_dir: Path) -> Path:
    raw = tmp_path / "raw" / "cdx"
    raw.mkdir(parents=True)
    shutil.copy(fixtures_dir / "cdx_era3_txt.json", raw / "era3_txt.json")
    return tmp_path


def test_build_captures_classifies_and_flags_plausibility(params: AcquireParams, acquire_dir: Path) -> None:
    captures, skipped = build_captures(params, acquire_dir)
    assert skipped == 1  # the folder address is not a single file
    assert [(c.month, c.digest, c.plausible) for c in captures] == [
        ("JAN13", "AAAA", True),
        ("JAN13", "BBBB", True),
        ("JAN13", "BBBB", True),
        ("FEB13", "CCCC", False),  # image MIME type: an error page
        ("MAR13", "DDDD", False),  # 404
    ]


def test_manifest_round_trip(params: AcquireParams, acquire_dir: Path) -> None:
    assert write_manifest(params, acquire_dir) == (5, 3, 1)
    again = read_manifest(acquire_dir)
    assert again == build_captures(params, acquire_dir)[0]


def test_read_manifest_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_manifest(tmp_path)


def test_coverage_report_lists_missing_and_multi_version_months(
    params: AcquireParams, acquire_dir: Path
) -> None:
    write_manifest(params, acquire_dir)
    full, summary = coverage_report(params, acquire_dir)
    assert "TXT: 1 of 3 months have a plausible capture" in summary
    assert "missing: FEB13 MAR13" in summary
    assert "more than one distinct file (compare these): 1" in summary
    assert "JAN13   3/2/3" in full  # 3 captures, 2 distinct files, era 3
