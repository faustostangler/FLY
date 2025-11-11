import pandas as pd
import pytest

from application.dtos.company_ratios_frame_dto import CompanyRatiosFrameDTO
from application.usecases.get_company_ratios_frame import (
    GetCompanyRatiosFrameRequest,
    GetCompanyRatiosFrameUseCase,
)
from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO
from domain.exceptions import DomainError
from domain.value_objects import SearchFilterTree


class DummyConfig:
    class Settings:
        app_name = "fly"
        version = "1"

    fly_settings = Settings()


class DummyLogger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None


class DummyRepository:
    def __init__(self, data):
        self._data = data

    def get_all(self, *, uow):
        return self._data

    def get_by_column_values(self, *, values, uow):
        return self._data


class DummyCompaniesEligiblePort:
    class Company:
        def __init__(self, company_name, ticker_codes):
            self.company_name = company_name
            self.ticker_codes = ticker_codes

    def list(self, *, uow, company_name):
        return [self.Company(company_name=company_name, ticker_codes=("TEST3",))]


class DummyCachePort:
    def initialize(self):
        return None

    def load(self, cache_key):
        return None

    def store(self, *, context, df, company_name):
        return {"path": "fake"}

    def invalidate_outdated(self, *, code_hash):
        return None


class DummyUow:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        return None


class DummyUowFactory:
    def __call__(self):
        return DummyUow()


class StubCacheService:
    def __init__(self, *_, **__):
        pass

    @staticmethod
    def build_code_hash(_items):
        return "hash"

    def get_or_compute(self, **kwargs):
        df = pd.DataFrame(
            {"02.03": [1.0, 2.0]},
            index=pd.to_datetime(["2024-01-01", "2024-02-01"]),
        )
        cache_info = CacheRatiosResultDTO(
            company_name=kwargs["company_name"],
            cache_key="hash-key",
            hit=False,
            entry=None,
        )
        return df, cache_info


class DummyRepositoryIndicators(DummyRepository):
    pass


class DummyRepositoryStatements(DummyRepository):
    pass


class DummyRepositoryQuotes(DummyRepository):
    pass


def test_get_company_ratios_frame_returns_dto(monkeypatch):
    config = DummyConfig()
    logger = DummyLogger()
    repo_indicators = DummyRepositoryIndicators([
        {"source": "s", "code": "c", "name": "n", "date": "2024-01-01", "value": 1}
    ])
    repo_statements = DummyRepositoryStatements([
        {
            "company_name": "TEST",
            "quarter": "2024-01-01",
            "value": 1,
            "account": "acc",
            "description": "desc",
            "grupo": "DFs Individuais",
            "quadro": "q",
            "version": "1",
        }
    ])
    repo_quotes = DummyRepositoryQuotes([
        {
            "ticker": "TEST3",
            "date": "2024-01-01",
            "open": 1,
            "low": 1,
            "high": 1,
            "close": 1,
            "adj_close": 1,
            "volume": 1,
        }
    ])
    cache_port = DummyCachePort()
    companies_port = DummyCompaniesEligiblePort()
    uow_factory = DummyUowFactory()

    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.CacheRatiosService",
        StubCacheService,
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.load_indicators",
        lambda *args, **kwargs: {"ind": pd.DataFrame({"date": ["2024-01-01"], "value": [1], "name": ["n"]})},
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.treat_indicators",
        lambda df: pd.DataFrame({"date": ["2024-01-01"], "value": [1]}),
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.load_statements",
        lambda *args, **kwargs: {"statements": pd.DataFrame({"quarter": ["2024-01-01"], "account": ["acc"], "description": ["desc"], "grupo": ["DFs Individuais"], "quadro": ["q"], "value": [1], "version": ["1"]})},
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.load_quotes",
        lambda *args, **kwargs: {"stock_1": pd.DataFrame({"ticker": ["TEST3"], "date": ["2024-01-01"], "open": [1], "low": [1], "high": [1], "close": [1], "adj_close": [1], "volume": [1]})},
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.treat_data",
        lambda snapshot, aggregate_method="last": snapshot,
    )
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.create_ratios",
        lambda data: pd.DataFrame({"02.03": [1.0, 2.0]}, index=pd.to_datetime(["2024-01-01", "2024-02-01"])),
    )

    usecase = GetCompanyRatiosFrameUseCase(
        config=config,
        logger=logger,
        repository_stock_quote=repo_quotes,
        repository_indicators=repo_indicators,
        repository_statements_fetched=repo_statements,
        cache_ratios=cache_port,
        companies_eligible_port=companies_port,
        uow_factory=uow_factory,
    )

    filter_tree = SearchFilterTree.from_raw({"and": [{"status": "ATIVO"}]})
    request = GetCompanyRatiosFrameRequest(company_name="TEST", filters=filter_tree)

    result: CompanyRatiosFrameDTO = usecase(request)

    assert isinstance(result.frame, pd.DataFrame)
    assert list(result.frame.columns) == ["02.03"]
    assert result.cache_info.hit is False
    assert result.meta["filters"] == filter_tree.to_dict()


def test_get_company_ratios_frame_requires_company_name(monkeypatch):
    monkeypatch.setattr(
        "application.usecases.get_company_ratios_frame.CacheRatiosService",
        StubCacheService,
    )
    usecase = GetCompanyRatiosFrameUseCase(  # type: ignore[arg-type]
        config=DummyConfig(),
        logger=DummyLogger(),
        repository_stock_quote=DummyRepositoryQuotes([]),
        repository_indicators=DummyRepositoryIndicators([]),
        repository_statements_fetched=DummyRepositoryStatements([]),
        cache_ratios=DummyCachePort(),
        companies_eligible_port=DummyCompaniesEligiblePort(),
        uow_factory=DummyUowFactory(),
    )

    with pytest.raises(DomainError):
        usecase(GetCompanyRatiosFrameRequest(company_name=""))
