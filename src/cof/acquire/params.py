"""Typed schema for ``config/acquire.yaml``."""

from pydantic import BaseModel

from cof.common.settings import Settings, load_yaml


class Plausibility(BaseModel):
    """What an index entry must look like to be considered a real file of one kind."""

    mime: str
    min_length: int


class AcquireParams(BaseModel):
    """Structured configuration of the acquire stage."""

    patterns: dict[str, str]
    cdx_limit: int
    cdx_fields: list[str]
    listing_url: str
    plausible: dict[str, Plausibility]
    expect_from: str
    expect_to: str
    pilot: list[tuple[str, str]]


def load_params(settings: Settings | None = None) -> AcquireParams:
    """Load and validate ``config/acquire.yaml``.

    Args:
        settings: Settings giving the configuration directory. Defaults to a fresh ``Settings()``.

    Returns:
        The validated parameters.
    """
    return AcquireParams.model_validate(load_yaml("acquire.yaml", settings))
