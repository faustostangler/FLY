from datetime import datetime
from unittest.mock import MagicMock

import pytest

from application.usecases.transform_statements import TransformStatementsUseCase
from domain.dto.statement_raw_dto import StatementRawDTO
from tests.conftest import DummyConfig


@pytest.fixture()
def sample_rows():
    return [
        StatementRawDTO(
            nsd="1",
            company_name="ACME",
            quarter="2020-03-31",
            version="V1",
            grupo="G",
            quadro="Q",
            account="01",
            description="d1",
            value=10.0,
        ),
        StatementRawDTO(
            nsd="2",
            company_name="ACME",
            quarter="2020-06-30",
            version="V1",
            grupo="G",
            quadro="Q",
            account="01",
            description="d2",
            value=20.0,
        ),
    ]


def test_execute_validates_and_runs_pipeline(monkeypatch, sample_rows):
    math_transformer = MagicMock()
    intel_transformer = MagicMock()

    math_transformer.transform.return_value = ["math"]
    intel_transformer.transform.return_value = ["intel"]

    monkeypatch.setattr(
        "infrastructure.utils.csv_utils.save_dtos_to_csv",
        lambda *args, **kwargs: None,
    )

    missing = {
        (
            "ACME",
            "01",
            "G",
            "Q",
            "V1",
        ): [datetime(2020, 9, 30)]
    }
    validate_mock = MagicMock(return_value=missing)
    monkeypatch.setattr(
        "application.usecases.transform_statements.validate_quarter_completeness",
        validate_mock,
    )

    logger = MagicMock()

    usecase = TransformStatementsUseCase(
        math_transformer,
        intel_transformer,
        DummyConfig(),
        logger,
    )
    result = usecase.execute(sample_rows)

    validate_mock.assert_called_once_with(sample_rows)
    logger.warning.assert_called_once_with(
        "After dedupe, account-group ('ACME', '01', 'G', 'Q', 'V1') missing quarters: ['2020-09-30']"
    )
    math_transformer.transform.assert_called_once()
    intel_transformer.transform.assert_called_once_with(["math"])
    assert result == ["intel"]
