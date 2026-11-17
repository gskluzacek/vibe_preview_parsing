from pathlib import Path

import pytest
from typer.testing import CliRunner

from cof.common.csvio import write_rows_atomic
from cof.normalize import cli

runner = CliRunner()
GOOD = (
    "PREVIEWS JANUARY VOL. 23 #1\r\nPAGE 1\r\nHEAD\r\n"
    "SS\tJAN13 0001\tBATMAN\t1/16/2013\tSRP: $2.99\t = $\t\r\n9\r\n"
)


def test_detect_lists_issues_without_changing_the_file(tmp_path: Path) -> None:
    path = tmp_path / "JAN13.txt"
    path.write_bytes(GOOD.encode())
    result = runner.invoke(cli.app, ["detect", str(path), "--month", "jan13"])
    assert result.exit_code == 0 and "I11" in result.output and "auto-derived" in result.output
    assert path.read_bytes() == GOOD.encode()


def test_run_normalizes_the_selected_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "txt").mkdir()
    (tmp_path / "txt" / "a.txt").write_bytes(GOOD.encode())
    row = {"month": "JAN13", "kind": "txt", "digest": "A", "timestamp": "2013", "path": "txt/a.txt",
           "status": "only_version", "reason_code": "", "reason_detail": ""}  # fmt: skip
    write_rows_atomic(tmp_path / "selection.csv", list(row), [row])
    monkeypatch.setenv("COF_ORIGINALS_DIR", str(tmp_path))
    monkeypatch.setenv("COF_NORMALIZED_DIR", str(tmp_path / "out"))
    result = runner.invoke(cli.app, ["run", "--months", "jan13"])
    assert result.exit_code == 0 and "1 files" in result.output
    table = (tmp_path / "out" / "2013_01.txt").read_text().splitlines()
    assert table[0].split("\t")[:5] == ["src_line", "page", "section", "merchandise_flag", "kind"]
    assert table[1].split("\t")[4] == "D" and "JAN13" not in table[1]
    assert table[3].split("\t")[5:] == ["SS", "2013-01-0001-0", "BATMAN", "2013-01-16", "SRP", "2.99"]


def test_rules_lists_required_and_optional_sets() -> None:
    result = runner.invoke(cli.app, ["rules"])
    assert result.exit_code == 0
    assert "F03  optional" in result.output and "I01  required" in result.output
