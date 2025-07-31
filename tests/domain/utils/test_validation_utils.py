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


def test_validate_quarter_completeness_detects_gap_per_group():
    rows = [
        _make_row("2021-03-31", "V1"),
        _make_row("2021-12-31", "V1"),
    ]

    missing_map = validate_quarter_completeness(rows)
    key = ("ACME", "ACC", "G", "Q", "V1")

    assert missing_map[key] == [
        datetime(2021, 6, 30),
        datetime(2021, 9, 30),
    ]
