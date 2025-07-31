from datetime import datetime

from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils.validation_utils import validate_quarter_completeness


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


def test_validate_quarter_completeness_detects_gap():
    rows = [
        _make_row("2021-03-31", "V1"),
        _make_row("2021-03-31", "V2"),
        _make_row("2021-09-30", "V1"),
        _make_row("2021-12-31", "V1"),
    ]

    missing = validate_quarter_completeness(rows)

    assert missing == [datetime(2021, 6, 30)]
