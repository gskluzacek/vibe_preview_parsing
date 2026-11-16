"""Typed project settings, read from ``COF_*`` environment variables and an optional ``.env`` file.

Simple scalar values (paths, delays, retry counts) live here. Structured configuration (URL patterns,
thresholds, rule metadata) lives in ``config/*.yaml`` and is read with :func:`load_yaml`.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/cof/common/settings.py -> repository root is three levels up from this file's directory.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Project-wide settings.

    Every field can be overridden with an environment variable named ``COF_<FIELD>`` (for example
    ``COF_WAYBACK_DELAY=0``) or a line in ``.env``. See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(env_prefix="COF_", env_file=PROJECT_ROOT / ".env", extra="ignore")

    config_dir: Path = PROJECT_ROOT / "config"
    acquire_dir: Path = PROJECT_ROOT / "data" / "acquire"
    originals_dir: Path = PROJECT_ROOT / "data" / "originals"
    normalized_dir: Path = PROJECT_ROOT / "data" / "normalized"

    wayback_delay: float = 2.0  # seconds to pause before every request to the archive
    wayback_retries: int = 5  # attempts per request before giving up
    wayback_timeout: float = 120.0  # seconds per request
    listing_every_days: int = 90  # sample one listing-page capture per this many days
    user_agent: str = "cof-archive-lister/0.2 (personal research; index queries)"


def load_yaml(name: str, settings: Settings | None = None) -> dict[str, Any]:
    """Read one YAML file from the configuration directory.

    Args:
        name: File name inside the configuration directory, for example ``"acquire.yaml"``.
        settings: Settings to take the configuration directory from. Defaults to a fresh ``Settings()``.

    Returns:
        The parsed mapping.

    Raises:
        ValueError: If the file does not contain a YAML mapping.
    """
    cfg_dir = (settings or Settings()).config_dir
    with open(cfg_dir / name, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{cfg_dir / name} must contain a YAML mapping")
    return data
