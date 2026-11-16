import pytest

from cof.common.months import from_period, month_index, months_between, to_period


def test_month_index_orders_by_year_then_month() -> None:
    assert month_index("JAN09") == (9, 0)
    assert month_index("DEC08") < month_index("JAN09") < month_index("FEB09")


def test_months_between_crosses_year_boundary() -> None:
    assert months_between("NOV09", "FEB10") == ["NOV09", "DEC09", "JAN10", "FEB10"]
    assert len(months_between("JAN09", "DEC25")) == 204


def test_to_period_all_months_sort_chronologically() -> None:
    codes = months_between("JAN09", "DEC25")
    periods = [to_period(c) for c in codes]
    assert periods == sorted(periods)  # the point of the naming scheme
    assert to_period("JAN13") == "2013_01"
    assert to_period("DEC25") == "2025_12"


def test_period_round_trip() -> None:
    for code in months_between("JAN09", "DEC25"):
        assert from_period(to_period(code)) == code


@pytest.mark.parametrize("bad", ["XXX13", "JAN1", "jan13", "2013-01"])
def test_to_period_rejects_bad_codes(bad: str) -> None:
    with pytest.raises(ValueError):
        to_period(bad)


@pytest.mark.parametrize("bad", ["2013_13", "2013_00", "1999_01", "13_01", "JAN13"])
def test_from_period_rejects_bad_periods(bad: str) -> None:
    with pytest.raises(ValueError):
        from_period(bad)
