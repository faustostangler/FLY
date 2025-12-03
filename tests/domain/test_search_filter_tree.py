import pandas as pd

from application.processors.filter_builder import FilterBuilder
from domain.value_objects import SearchFilterTree
from infrastructure.utils.pandas_visitor import PandasVisitor


def test_filtered_by_fields_keeps_only_allowed_leaves():
    tree_raw = {
        "and": [
            {"industry_segment": {"in": ["TECNOLOGIA"]}},
            {"date": {">=": "2020-01-01"}},
        ]
    }
    tree = SearchFilterTree.from_raw(tree_raw)

    filtered = tree.filtered_by_fields({"date"})

    assert filtered is not None
    assert filtered.to_dict() == {"and": [{"date": {">=": "2020-01-01"}}]}


def test_filtered_by_fields_returns_none_when_all_pruned():
    tree_raw = {"industry_segment": {"in": ["TECNOLOGIA"]}}
    tree = SearchFilterTree.from_raw(tree_raw)

    assert tree.filtered_by_fields({"date"}) is None


def test_filtered_tree_works_with_filter_builder():
    tree_raw = {
        "and": [
            {"industry_segment": {"in": ["TECNOLOGIA"]}},
            {"date": {">=": "2020-01-01"}},
        ]
    }
    tree = SearchFilterTree.from_raw(tree_raw)
    filtered = tree.filtered_by_fields({"date"})

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-01-01", "2021-05-10"]),
            "value": [1, 2],
        }
    )

    spec = FilterBuilder().build_spec(filtered.to_dict())
    mask = spec.accept(PandasVisitor(), df)

    filtered_df = df[mask]

    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["value"] == 2
