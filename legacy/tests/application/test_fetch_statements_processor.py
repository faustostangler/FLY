from unittest.mock import MagicMock

from application.processors.fetch_statements_processor import FetchStatementsProcessor
from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto.nsd_dto import NsdDTO
from domain.ports import (
    RepositoryCompanyDataPort,
    RepositoryNsdPort,
    RepositoryStatementFetchedPort,
    StatementRawRepositoryPort,
)
from domain.ports.scraper_ports import StatementsRawcraperPort
from tests.conftest import DummyConfig, DummyLogger


def test_fetch_statements_calls_usecase(monkeypatch):
    dummy_config = DummyConfig()

    mock_usecase_cls = MagicMock(spec=FetchStatementsUseCase)
    mock_usecase_inst = MagicMock()
    mock_usecase_cls.return_value = mock_usecase_inst
    monkeypatch.setattr(
        "application.processors.fetch_statements_processor.FetchStatementsUseCase",
        mock_usecase_cls,
    )

    company_repo = MagicMock(spec=RepositoryCompanyDataPort)
    nsd_repo = MagicMock(spec=RepositoryNsdPort)
    stmt_repo = MagicMock(spec=StatementRawRepositoryPort)
    rows_repo = MagicMock(spec=RepositoryStatementFetchedPort)
    source = MagicMock(spec=StatementsRawcraperPort)
    collector = MagicMock()
    worker_pool = MagicMock()

    processor = FetchStatementsProcessor(
        logger=DummyLogger(),
        source=source,
        fetched_statements_repo=rows_repo,
        company_repo=company_repo,
        nsd_repo=nsd_repo,
        raw_statement_repo=stmt_repo,
        config=dummy_config,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
        max_workers=3,
    )

    mock_usecase_cls.assert_called_once_with(
        logger=processor.logger,
        source=source,
        fetched_statements_repo=rows_repo,
        raw_statement_repository=stmt_repo,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
        config=dummy_config,
        max_workers=3,
    )

    targets = [MagicMock(spec=NsdDTO)]
    monkeypatch.setattr(processor, "_build_targets", lambda: targets)

    result = processor.run(save_callback="cb", threshold=5)

    mock_usecase_inst.fetch_statement_rows.assert_called_once_with(
        batch_rows=targets, save_callback="cb", threshold=5
    )
    assert result == mock_usecase_inst.fetch_statement_rows.return_value
