from unittest.mock import MagicMock

from application.services.statement_fetch_service import StatementFetchService
from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto.nsd_dto import NsdDTO
from domain.ports import (
    NSDRepositoryPort,
    RawStatementScraperPort,
    SqlAlchemyCompanyDataRepositoryPort,
    SqlAlchemyParsedStatementRepositoryPort,
)
from infrastructure.repositories import SqlAlchemyRawStatementRepository
from tests.conftest import DummyConfig, DummyLogger


def test_fetch_statements_calls_usecase(monkeypatch):
    dummy_config = DummyConfig()

    mock_usecase_cls = MagicMock(spec=FetchStatementsUseCase)
    mock_usecase_inst = MagicMock()
    mock_usecase_cls.return_value = mock_usecase_inst
    monkeypatch.setattr(
        "application.services.statement_fetch_service.FetchStatementsUseCase",
        mock_usecase_cls,
    )

    company_repo = MagicMock(spec=SqlAlchemyCompanyDataRepositoryPort)
    nsd_repo = MagicMock(spec=NSDRepositoryPort)
    stmt_repo = MagicMock(spec=SqlAlchemyRawStatementRepository)
    rows_repo = MagicMock(spec=SqlAlchemyParsedStatementRepositoryPort)
    source = MagicMock(spec=RawStatementScraperPort)
    collector = MagicMock()
    worker_pool = MagicMock()

    service = StatementFetchService(
        logger=DummyLogger(),
        source=source,
        parsed_statements_repo=rows_repo,
        company_repo=company_repo,
        nsd_repo=nsd_repo,
        raw_statement_repo=stmt_repo,
        config=dummy_config,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
        max_workers=3,
    )

    mock_usecase_cls.assert_called_once_with(
        logger=service.logger,
        source=source,
        parsed_statements_repo=rows_repo,
        raw_statement_repository=stmt_repo,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
        config=dummy_config,
        max_workers=3,
    )

    targets = [MagicMock(spec=NsdDTO)]
    monkeypatch.setattr(service, "_build_targets", lambda: targets)

    result = service.fetch_statements(save_callback="cb", threshold=5)

    mock_usecase_inst.fetch_statement_rows.assert_called_once_with(
        batch_rows=targets, save_callback="cb", threshold=5
    )
    assert result == mock_usecase_inst.fetch_statement_rows.return_value
