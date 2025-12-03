from unittest.mock import MagicMock

from application.usecases.fetch_statements import FetchStatementsUseCase
from domain.dto.nsd_dto import NsdDTO
from domain.ports import RepositoryStatementFetchedPort, StatementRawRepositoryPort
from domain.ports.scraper_ports import StatementsRawcraperPort
from tests.conftest import DummyConfig, DummyLogger


def _make_nsd(nsd: int) -> NsdDTO:
    return NsdDTO(
        nsd=str(nsd),
        company_name="Comp",
        quarter=None,
        version=None,
        nsd_type=None,
        dri=None,
        auditor=None,
        responsible_auditor=None,
        protocol=None,
        sent_date=None,
        reason=None,
    )


def test_fetch_statement_rows_skips_existing(monkeypatch):
    source = MagicMock(spec=StatementsRawcraperPort)
    rows_repo = MagicMock(spec=RepositoryStatementFetchedPort)
    stmt_repo = MagicMock(spec=StatementRawRepositoryPort)
    stmt_repo.get_all_primary_keys = MagicMock(return_value={1})

    collector = MagicMock()
    worker_pool = MagicMock()

    usecase = FetchStatementsUseCase(
        logger=DummyLogger(),
        source=source,
        fetched_statements_repo=rows_repo,
        raw_statement_repository=stmt_repo,
        metrics_collector=collector,
        worker_pool_executor=worker_pool,
        config=DummyConfig(),
        max_workers=2,
    )

    mock_fetch_all = MagicMock(return_value=[("result", [])])
    monkeypatch.setattr(usecase, "fetch_all", mock_fetch_all)

    targets = [_make_nsd(1), _make_nsd(2)]
    result = usecase.fetch_statement_rows(targets, save_callback="cb", threshold=5)

    stmt_repo.get_all_primary_keys.assert_not_called()
    mock_fetch_all.assert_called_once_with(
        targets=targets, save_callback="cb", threshold=5
    )
    assert result == mock_fetch_all.return_value
