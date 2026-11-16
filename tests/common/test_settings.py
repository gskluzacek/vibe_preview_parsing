from pathlib import Path

import pytest

from cof.common.settings import Settings, load_yaml


def test_defaults_and_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    assert Settings().wayback_retries == 5
    monkeypatch.setenv("COF_WAYBACK_DELAY", "0")
    assert Settings().wayback_delay == 0.0


def test_load_yaml_reads_project_config() -> None:
    data = load_yaml("acquire.yaml")
    assert "patterns" in data and "pilot" in data


def test_load_yaml_rejects_non_mapping(tmp_path: Path) -> None:
    (tmp_path / "bad.yaml").write_text("- a\n- b\n")
    with pytest.raises(ValueError):
        load_yaml("bad.yaml", Settings(config_dir=tmp_path))
