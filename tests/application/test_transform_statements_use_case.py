from unittest.mock import MagicMock

from application.ports import StatementTransformerPort
from application.usecases.transform_statements import TransformStatementsUseCase
from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from tests.conftest import DummyConfig


class DummyTransformer(StatementTransformerPort):
    def transform(self, rows):
        return [
            ParsedStatementDTO(
                nsd=r.nsd,
                company_name=r.company_name,
                quarter=r.quarter,
                version=r.version,
                grupo=r.grupo,
                quadro=r.quadro,
                account=r.account,
                description=r.description,
                value=r.value,
            )
            for r in rows
        ]


def _make_row(quarter: str, version: str) -> RawStatementDTO:
    return RawStatementDTO(
        nsd="1",
        company_name="ACME",
        quarter=quarter,
        version=version,
        grupo="G",
        quadro="Q",
        account="ACC",
        description="",
        value=0.0,
    )


def test_usecase_logs_missing_and_deduplicates():
    logger = MagicMock()
    usecase = TransformStatementsUseCase(
        math_transformer=DummyTransformer(),
        intel_transformer=DummyTransformer(),
        config=DummyConfig(),
        logger=logger,
    )

    rows = [
        _make_row("2021-03-31", "V1"),
        _make_row("2021-03-31", "V2"),
        _make_row("2021-09-30", "V1"),
        _make_row("2021-09-30", "V2"),
        _make_row("2021-12-31", "V1"),
    ]

    result = usecase.execute(rows)

    logger.warning.assert_any_call(
        "Group %s missing quarters: %s",
        ("ACME", "ACC", "G", "Q", "V1"),
        ["2021-06-30"],
    )
    logger.warning.assert_any_call(
        "Group %s missing quarters: %s",
        ("ACME", "ACC", "G", "Q", "V2"),
        ["2021-06-30"],
    )
    assert logger.warning.call_count == 2

    mapping = {(r.quarter, r.version) for r in result}
    assert ("2021-03-31", "V2") in mapping
    assert ("2021-09-30", "V2") in mapping
    assert ("2021-12-31", "V1") in mapping
    assert len(result) == 3
