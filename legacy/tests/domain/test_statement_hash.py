from domain.dto.statement_raw_dto import StatementRawDTO
from domain.utils.statement_hash import compute_hash


def test_compute_hash_consistent_order():
    rows = [
        StatementRawDTO.from_dict(
            {
                "nsd": 1,
                "company_name": "A",
                "quarter": "2020-03-31",
                "version": "1",
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
                "company_name": "A",
                "quarter": "2020-06-30",
                "version": "1",
                "grupo": "G",
                "quadro": "Q",
                "account": "02",
                "description": "d2",
                "value": 2,
            }
        ),
    ]

    reversed_rows = list(reversed(rows))
    assert compute_hash(rows) == compute_hash(reversed_rows)
