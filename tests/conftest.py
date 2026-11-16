"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from cof.acquire.params import AcquireParams, Plausibility


@pytest.fixture
def params() -> AcquireParams:
    """Small acquire configuration used by tests (does not read config/acquire.yaml)."""
    return AcquireParams(
        patterns={"era3_txt": "previewsworld.com/Catalog/CustomerOrderForm/TXT/*"},
        cdx_limit=1000,
        cdx_fields=["timestamp", "original", "statuscode", "mimetype", "length", "digest"],
        listing_url="previewsworld.com/Catalog/CustomerOrderForms",
        plausible={
            "txt": Plausibility(mime="text/plain", min_length=5000),
            "pdf": Plausibility(mime="application/pdf", min_length=100000),
        },
        expect_from="JAN13",
        expect_to="MAR13",
        pilot=[("JAN13", "txt")],
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Directory with recorded test inputs."""
    return Path(__file__).parent / "fixtures"
