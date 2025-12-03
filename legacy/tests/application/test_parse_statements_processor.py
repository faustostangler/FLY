from unittest.mock import MagicMock

from application.processors.parse_statements_processor import ParseStatementsProcessor
from application.usecases.parse_and_classify_statements import (
    ParseAndClassifyStatementsUseCase,
)
from domain.dto import NsdDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.ports import RepositoryStatementFetchedPort
from tests.conftest import DummyConfig, DummyLogger


def test_parse_statements_invokes_usecase_and_finalize(monkeypatch):
    dummy_config = DummyConfig()

    mock_usecase_cls = MagicMock(spec=ParseAndClassifyStatementsUseCase)
    mock_usecase_inst = MagicMock()
    mock_usecase_cls.return_value = mock_usecase_inst
    monkeypatch.setattr(
        "application.processors.parse_statements_processor.ParseAndClassifyStatementsUseCase",
        mock_usecase_cls,
    )

    repository = MagicMock(spec=RepositoryStatementFetchedPort)
    worker_pool = MagicMock()
    collector = MagicMock()

    processor = ParseStatementsProcessor(
        logger=DummyLogger(),
        repository=repository,
        config=dummy_config,
        worker_pool_executor=worker_pool,
        metrics_collector=collector,
        max_workers=2,
    )

    mock_usecase_cls.assert_called_once_with(
        logger=processor.logger, repository=repository, config=dummy_config
    )

    parse_all = MagicMock()
    monkeypatch.setattr(processor, "_parse_all", parse_all)

    fetched = [(MagicMock(spec=NsdDTO), [MagicMock(spec=StatementRawDTO)])]

    result = processor.run(fetched)

    parse_all.assert_called_once_with(fetched)
    mock_usecase_inst.finalize.assert_called_once()
    assert result == parse_all.return_value
