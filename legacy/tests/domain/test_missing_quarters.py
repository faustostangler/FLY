from datetime import datetime

from domain.utils.math_utils import find_missing_quarters


def test_find_missing_quarters_basic():
    dates = [datetime(2020, 3, 31), datetime(2020, 12, 31)]
    missing = find_missing_quarters(dates)
    assert missing == [datetime(2020, 6, 30), datetime(2020, 9, 30)]


def test_find_missing_quarters_unsorted_duplicates():
    dates = [
        datetime(2020, 12, 31),
        datetime(2020, 3, 31),
        datetime(2020, 6, 30),
        datetime(2020, 3, 31),
    ]
    missing = find_missing_quarters(dates)
    assert missing == [datetime(2020, 9, 30)]
