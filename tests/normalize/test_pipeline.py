from pathlib import Path

from cof.common.csvio import read_rows, write_rows_atomic
from cof.common.settings import Settings
from cof.normalize.pipeline import run_pipeline

GOOD = "\r\n".join(
    [
        "PREVIEWS JANUARY VOL. 23 #1",
        "PAGE 1",
        "HEAD",
        "SS\tJAN13 0001\tBATMAN\t01/16/13\tSRP: $2.99\t = $\t",
        "9",
        "",
    ]
)


def setup(tmp_path: Path) -> Settings:
    orig = tmp_path / "originals"
    (orig / "txt").mkdir(parents=True)
    files = {"a.txt": GOOD.encode("cp1252"), "b.txt": GOOD.replace("JAN13", "FEB13").encode("cp1252")}
    rows = []
    for name, month, status in (("a.txt", "JAN13", "selected"), ("b.txt", "FEB13", "not_used")):
        (orig / "txt" / name).write_bytes(files[name])
        rows.append(
            {
                "month": month,
                "kind": "txt",
                "digest": name,
                "timestamp": "2013",
                "path": f"txt/{name}",
                "status": status,
                "reason_code": "",
                "reason_detail": "",
            }
        )
    write_rows_atomic(orig / "selection.csv", list(rows[0]), rows)
    return Settings(originals_dir=orig, normalized_dir=tmp_path / "normalized")


def test_run_writes_only_selected_months_with_sortable_names(tmp_path: Path) -> None:
    settings = setup(tmp_path)
    result = run_pipeline(settings, None, lambda s: None)
    assert (result.files, result.rejected) == (1, 0)
    assert sorted(p.name for p in settings.normalized_dir.glob("*.txt")) == ["2013_01.txt"]
    summary = read_rows(settings.normalized_dir / "summary.csv")
    assert summary[0]["period"] == "2013_01" and summary[0]["source_encoding"] == "ascii"
    assert (settings.normalized_dir / "issues.csv").exists()


def test_full_run_removes_stale_outputs_but_partial_run_does_not(tmp_path: Path) -> None:
    settings = setup(tmp_path)
    run_pipeline(settings, None, lambda s: None)
    stale = settings.normalized_dir / "2001_01.txt"
    stale.write_text("old\n")
    other = settings.normalized_dir / "notes.txt"
    other.write_text("keep\n")
    run_pipeline(settings, {"JAN13"}, lambda s: None)
    assert stale.exists()  # a partial run leaves other files alone
    result = run_pipeline(settings, None, lambda s: None)
    assert result.removed == 1 and not stale.exists() and other.exists()


def test_output_is_deterministic(tmp_path: Path) -> None:
    settings = setup(tmp_path)
    run_pipeline(settings, None, lambda s: None)
    first = {p.name: p.read_bytes() for p in settings.normalized_dir.iterdir()}
    run_pipeline(settings, None, lambda s: None)
    assert first == {p.name: p.read_bytes() for p in settings.normalized_dir.iterdir()}
