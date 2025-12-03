from datetime import datetime

from domain.dto.statement_raw_dto import StatementRawDTO
from domain.utils.validation_utils import validate_quarter_completeness


def test_validate_quarter_completeness_detects_missing():
    rows = [
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2020-03-31",
            version="V1",
            grupo="G",
            quadro="Q",
            account="01",
            description="",
            value=1.0,
        ),
        StatementRawDTO(
            nsd="2",
            company_name="ACME",
            quarter="2020-12-31",
            version="V1",
            grupo="G",
            quadro="Q",
            account="01",
            description="",
            value=2.0,
        ),
    ]

    missing = validate_quarter_completeness(rows)
    key = ("ACME", "01", "G", "Q", "")
    assert missing[key] == [datetime(2020, 6, 30), datetime(2020, 9, 30)]
