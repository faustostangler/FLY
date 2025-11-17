import copy

from infrastructure.utils.normalization import clean_dict_fields
from tests.conftest import DummyLogger


def test_clean_dict_fields_non_mutating():
    entry = {"name": "Acme!", "listed": "01/02/2020"}
    original = copy.deepcopy(entry)

    cleaned = clean_dict_fields(
        entry,
        text_keys=["name"],
        date_keys=["listed"],
        logger=DummyLogger(),
    )

    assert cleaned["name"] == "ACME"
    assert hasattr(cleaned["listed"], "year") and cleaned["listed"].year == 2020
    assert entry == original
