from pathlib import Path

import pytest

from cof.common.csvio import read_rows, write_rows_atomic


def test_round_trip_and_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "x.csv"
    assert read_rows(path) == []
    write_rows_atomic(path, ["a", "b"], [{"a": 1, "b": "é"}, {"a": 2, "b": "x,y"}])
    assert read_rows(path) == [{"a": "1", "b": "é"}, {"a": "2", "b": "x,y"}]
    assert not path.with_name("x.csv.tmp").exists()


def test_failed_write_leaves_existing_file_intact(tmp_path: Path) -> None:
    path = tmp_path / "x.csv"
    write_rows_atomic(path, ["a"], [{"a": 1}])
    with pytest.raises(ValueError):
        write_rows_atomic(path, ["a"], [{"zzz": 1}])  # key not in fieldnames
    assert read_rows(path) == [{"a": "1"}]
