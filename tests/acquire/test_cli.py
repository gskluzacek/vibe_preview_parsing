import json
import shutil
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from cof.acquire import cli
from cof.acquire.index import fetch_index
from cof.acquire.params import AcquireParams
from cof.acquire.wayback import WaybackClient

runner = CliRunner()


@pytest.fixture
def workdir(tmp_path: Path, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the CLI at a scratch data directory containing one recorded index file."""
    raw = tmp_path / "acquire" / "raw" / "cdx"
    raw.mkdir(parents=True)
    shutil.copy(fixtures_dir / "cdx_era3_txt.json", raw / "era3_txt.json")
    monkeypatch.setenv("COF_ACQUIRE_DIR", str(tmp_path / "acquire"))
    monkeypatch.setenv("COF_ORIGINALS_DIR", str(tmp_path / "originals"))
    return tmp_path


def test_manifest_report_and_dry_run_fetch(workdir: Path) -> None:
    result = runner.invoke(cli.app, ["manifest"])
    assert result.exit_code == 0 and "3 plausible" in result.output
    assert (workdir / "acquire" / "manifest.csv").exists()

    result = runner.invoke(cli.app, ["report"])
    assert result.exit_code == 0 and "COF coverage" in result.output
    assert (workdir / "acquire" / "report.txt").exists()

    result = runner.invoke(cli.app, ["fetch", "--months", "JAN13", "--kinds", "txt", "--dry-run"])
    assert result.exit_code == 0
    assert result.output.count("would") == 2  # two distinct versions of JAN13
    assert not (workdir / "originals" / "downloads.csv").exists()


def test_fetch_requires_a_selection(workdir: Path) -> None:
    runner.invoke(cli.app, ["manifest"])
    result = runner.invoke(cli.app, ["fetch"])
    assert result.exit_code != 0


def test_fetch_index_stores_raw_answer(tmp_path: Path, params: AcquireParams) -> None:
    rows = [["timestamp", "original"], ["2013", "http://a"]]
    client = WaybackClient(
        delay=0,
        retries=1,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=rows)),
        sleep=lambda s: None,
    )
    counts = fetch_index(client, params, tmp_path)
    assert counts == {"era3_txt": 1}
    stored = json.loads((tmp_path / "raw" / "cdx" / "era3_txt.json").read_text())
    assert stored["rows"] == [["2013", "http://a"]] and stored["pattern"].endswith("TXT/*")
