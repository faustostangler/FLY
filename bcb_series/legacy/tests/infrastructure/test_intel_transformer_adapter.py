from domain.dto.statement_raw_dto import StatementRawDTO
from domain.services import StatementClassificationService
from infrastructure.config import Config
from infrastructure.transformers import IntelStatementTransformerAdapter


def test_intel_adapter_full_flow():
    rows = [
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2024-03-31",
            version="1",
            grupo="G",
            quadro="Q",
            account="00.01.01",
            description="Ações ON Ordinárias",
            value=10.0,
        ),
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2024-03-31",
            version="2",
            grupo="G",
            quadro="Q",
            account="00.01.01",
            description="Ações ON Ordinárias",
            value=11.0,
        ),
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2024-06-30",
            version="1",
            grupo="G",
            quadro="Q",
            account="06.01",
            description="Cumulative",
            value=30.0,
        ),
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2024-09-30",
            version="1",
            grupo="G",
            quadro="Q",
            account="06.01",
            description="Cumulative",
            value=60.0,
        ),
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2024-12-31",
            version="1",
            grupo="G",
            quadro="Q",
            account="06.01",
            description="Cumulative",
            value=100.0,
        ),
    ]

    adapter = IntelStatementTransformerAdapter(
        config=Config(), classification_service=StatementClassificationService()
    )
    result = adapter.transform(rows)

    assert len(result) == 5
    first = [r for r in result if r.quarter == "2024-03-31" and r.version == "2"][0]
    assert first.value == 11.0
    cum_values = [r for r in result if r.account == "06.01"]
    assert [r.value for r in cum_values] == [30.0, 60.0, 100.0]
