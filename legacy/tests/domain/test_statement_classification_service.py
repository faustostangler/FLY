from domain.dto.statement_raw_dto import StatementRawDTO
from domain.services import StatementClassificationService
from domain.utils.criteria_node import CriteriaNode


def build_row(account: str) -> StatementRawDTO:
    return StatementRawDTO(
        nsd="1",
        company_name="ACME",
        quarter="2024-03-31",
        version="1",
        grupo="G",
        quadro="Q",
        account=account,
        description="",
        value=1.0,
    )


def test_classify_recurses_through_children():
    rows = [
        build_row("1"),
        build_row("1.01"),
        build_row("1.01.01"),
        build_row("1.02"),
    ]

    tree = [
        CriteriaNode(
            target_line="1 - Root",
            criteria=[("account", "equals", "1")],
            children=[
                CriteriaNode(
                    target_line="1.01 - Child",
                    criteria=[("account", "equals", "1.01")],
                    children=[
                        CriteriaNode(
                            target_line="1.01.01 - Grand",
                            criteria=[("account", "equals", "1.01.01")],
                            children=[],
                        )
                    ],
                ),
                CriteriaNode(
                    target_line="1.02 - Child",
                    criteria=[("account", "equals", "1.02")],
                    children=[],
                ),
            ],
        )
    ]

    service = StatementClassificationService()
    result = service.classify(rows, tree)
    accounts = [r.account for r in result]
    assert accounts == ["1", "1.01", "1.01.01", "1.02"]


def test_classify_no_root_match():
    rows = [build_row("2"), build_row("2.01")]
    tree = [
        CriteriaNode(
            target_line="1 - Root",
            criteria=[("account", "equals", "1")],
            children=[
                CriteriaNode(
                    target_line="1.01 - Child",
                    criteria=[("account", "equals", "1.01")],
                    children=[],
                )
            ],
        )
    ]

    service = StatementClassificationService()
    result = service.classify(rows, tree)
    assert result == []


def test_classify_only_root_match():
    rows = [build_row("1")]
    tree = [
        CriteriaNode(
            target_line="1 - Root",
            criteria=[("account", "equals", "1")],
            children=[
                CriteriaNode(
                    target_line="1.01 - Child",
                    criteria=[("account", "equals", "1.01")],
                    children=[],
                )
            ],
        )
    ]

    service = StatementClassificationService()
    result = service.classify(rows, tree)
    assert [r.account for r in result] == ["1"]
