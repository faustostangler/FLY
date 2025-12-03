import types
from unittest.mock import MagicMock

from application.usecases.sync_companies import SyncCompanyDataUseCase
from domain.dto.company_data_dto import CompanyDataDTO
from domain.dto.execution_result_dto import ExecutionResultDTO
from domain.dto.metrics_dto import MetricsDTO
from domain.dto.sync_companies_result_dto import SyncCompanyDataResultDTO
from domain.ports import RepositoryCompanyDataPort, ScraperCompanyDataPort
from tests.conftest import DummyLogger


def test_execute_converts_and_saves():
    repo = MagicMock(spec=RepositoryCompanyDataPort)
    repo.iter_existing_by_columns = MagicMock(return_value=iter([("SKIP",)]))

    raw = types.SimpleNamespace(
        cvm_code="001",
        company_name="Acme",
        issuing_company="ACM",
        ticker_codes=["ACM"],
        isin_codes=["BRACM"],
        trading_name="Acme",
        industry_sector="Tech",
        industry_subsector="Software",
        industry_segment="IT",
        listing_segment="Novo Mercado",
        activity="Development",
        registrar="EXCHANGE",
        cnpj="00.000.000/0001-91",
        website="example.com",
        company_type="SA",
        status="active",
        listing_date=None,
        other_codes=[],
        industry_classification=None,
        industry_classification_eng=None,
        company_segment=None,
        company_segment_eng=None,
        company_category=None,
        institution_common=None,
        institution_preferred=None,
        market=None,
        market_indicator=None,
        code=None,
        has_bdr=None,
        type_bdr=None,
        has_quotation=None,
        has_emissions=None,
        date_quotation=None,
        last_date=None,
    )

    def fake_fetch_all(
        threshold=None,
        existing_codes=None,
        save_callback=None,
        max_workers=None,
    ):
        assert existing_codes == ["SKIP"]
        if save_callback:
            save_callback([raw])
        metrics = MetricsDTO(elapsed_time=0.0, network_bytes=100, processing_bytes=0)
        return ExecutionResultDTO(items=[raw], metrics=metrics)

    scraper = MagicMock(spec=ScraperCompanyDataPort)
    scraper.fetch_all.side_effect = fake_fetch_all
    scraper.metrics_collector = types.SimpleNamespace(network_bytes=100)

    usecase = SyncCompanyDataUseCase(
        logger=DummyLogger(),
        repository=repo,
        scraper=scraper,
        max_workers=2,
    )

    result = usecase.synchronize_companies()

    repo.iter_existing_by_columns.assert_called_once()
    scraper.fetch_all.assert_called_once()
    repo.save_all.assert_called_once()
    saved = repo.save_all.call_args.args[0]
    assert isinstance(saved[0], CompanyDataDTO)
    assert saved[0].cvm_code == "001"

    assert isinstance(result, SyncCompanyDataResultDTO)
    assert result.processed_count == 1
    assert result.skipped_count == 1
    assert result.bytes_downloaded == 100
