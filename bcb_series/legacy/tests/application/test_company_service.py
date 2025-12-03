from unittest.mock import MagicMock

# from application.services.company_services import CompanyDataService
from application.services.company_data_service import CompanyDataService
from application.usecases.sync_companies import SyncCompanyDataUseCase
from domain.ports import RepositoryCompanyDataPort, ScraperCompanyDataPort
from tests.conftest import DummyConfig, DummyLogger


def test_sync_companies_calls_usecase(monkeypatch):
    dummy_config = DummyConfig()
    dummy_config.global_settings.max_workers = 3

    mock_usecase_cls = MagicMock(spec=SyncCompanyDataUseCase)
    mock_usecase_inst = MagicMock()
    mock_usecase_cls.return_value = mock_usecase_inst
    monkeypatch.setattr(
        "application.services.company_data_service.SyncCompanyDataUseCase",
        mock_usecase_cls,
    )

    repo = MagicMock(spec=RepositoryCompanyDataPort)
    scraper = MagicMock(spec=ScraperCompanyDataPort)

    service = CompanyDataService(
        config=dummy_config,
        logger=DummyLogger(),
        repository=repo,
        scraper=scraper,
    )

    mock_usecase_cls.assert_called_once_with(
        logger=service.logger,
        repository=repo,
        scraper=scraper,
        max_workers=3,
    )

    result = service.sync_companies()

    mock_usecase_inst.synchronize_companies.assert_called_once()
    assert result == mock_usecase_inst.synchronize_companies.return_value
