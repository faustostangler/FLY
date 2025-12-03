from domain.dto.statement_raw_dto import StatementRawDTO
from domain.utils.version_utils import filter_latest_versions


def test_filter_latest_versions_keeps_highest():
    rows = [
        StatementRawDTO.from_dict(
            {
                "nsd": 1,
                "company_name": "ACME",
                "quarter": "2020-03-31",
                "version": "V1",
                "grupo": "G",
                "quadro": "Q",
                "account": "01",
                "description": "d1",
                "value": 1,
            }
        ),
        StatementRawDTO.from_dict(
            {
                "nsd": 2,
                "company_name": "ACME",
                "quarter": "2020-03-31",
                "version": "V2",
                "grupo": "G",
                "quadro": "Q",
                "account": "01",
                "description": "d2",
                "value": 2,
            }
        ),
        StatementRawDTO.from_dict(
            {
                "nsd": 3,
                "company_name": "ACME",
                "quarter": "2020-06-30",
                "version": "V1",
                "grupo": "G",
                "quadro": "Q",
                "account": "01",
                "description": "d3",
                "value": 3,
            }
        ),
    ]

    result = filter_latest_versions(rows)
    mapping = {
        (r.company_name, r.account, r.grupo, r.quadro, r.quarter): r.version
        for r in result
    }

    assert mapping[("ACME", "01", "G", "Q", "2020-03-31")] == "V2"
    assert mapping[("ACME", "01", "G", "Q", "2020-06-30")] == "V1"
    assert len(result) == 2
