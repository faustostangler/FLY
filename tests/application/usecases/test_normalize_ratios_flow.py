from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Iterable, Sequence

import pandas as pd
import pytest

from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from application.usecases.normalize_ratios import NormalizeUseCase
from application.usecases.companies_eligible import (
    CompaniesEligibleUseCase,
)
from domain.dtos import (
    CompanyDataDTO,
    CacheRatiosEntryDTO,
    CacheRatiosResultDTO,
    StatementFetchedDTO,
    WorkerTaskDTO,
)
from domain.dtos.stock_quote_dto import StockQuoteDTO
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.uow.uow import UowFactory


class DummyLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def log(self, message: str, level: str = "info", **_: object) -> None:
        self.records.append((message, level))


class InMemoryCompanyRepository:
    def __init__(self, companies: Sequence[CompanyDataDTO]) -> None:
        self._companies = list(companies)

    def get_all(self, *, uow, batch_size: int | None = None) -> list[CompanyDataDTO]:  # noqa: ARG002
        return list(self._companies)


class InMemoryStatementRepository:
    def __init__(self, statements: Sequence[StatementFetchedDTO]) -> None:
        self._statements = list(statements)

    def get_unique_by_column(self, column_name: str, *, uow) -> list[str]:  # noqa: ARG002
        if column_name != "company_name":
            return []
        return sorted({row.company_name for row in self._statements if row.company_name})

    def get_by_column_values(self, values, *, uow, batch_size=None):  # noqa: ANN001, ARG002, D417
        criteria = dict(values) if not isinstance(values, dict) else values
        target = criteria.get("company_name")
        if target is None:
            return []
        if isinstance(target, Iterable) and not isinstance(target, str):
            names = {name for name in target if name}
        else:
            names = {target}
        return [row for row in self._statements if row.company_name in names]


class InMemoryStockQuoteRepository:
    def __init__(self, quotes: Sequence[StockQuoteDTO]) -> None:
        self._quotes = list(quotes)

    def get_unique_by_column(self, column_name: str, *, uow) -> list[str]:  # noqa: ARG002
        if column_name != "ticker":
            return []
        return sorted({row.ticker for row in self._quotes if row.ticker})

    def get_by_column_values(self, values, *, uow, batch_size=None):  # noqa: ANN001, ARG002, D417
        criteria = dict(values) if not isinstance(values, dict) else values
        target = criteria.get("ticker")
        if target is None:
            return []
        if isinstance(target, Iterable) and not isinstance(target, str):
            tickers = {ticker for ticker in target if ticker}
        else:
            tickers = {target}
        return [row for row in self._quotes if row.ticker in tickers]


class DummyIndicatorsRepository:
    def get_all(self, *, uow, batch_size=None):  # noqa: ANN001, ARG002, D417
        return []


class DummyCacheRatiosPort:
    def initialize(self) -> None:
        return None

    def load(self, cache_key: str):  # noqa: D401
        return None

    def store(self, *, context, df, company_name):  # noqa: ANN001, ARG002, D401
        raise NotImplementedError

    def invalidate_outdated(self, *, code_hash: str) -> None:  # noqa: ARG002
        return None


class FakeCacheRatiosService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_or_compute(
        self,
        *,
        company_name: str,
        quotes,
        statements,
        indicators,
        compute_fn,
        code_hash: str,
    ) -> tuple[pd.DataFrame, CacheRatiosResultDTO]:
        del quotes, statements, indicators, compute_fn
        self.calls.append(company_name)
        entry = CacheRatiosEntryDTO(
            cache_key=f"{company_name}-cache",
            file_path="/tmp/fake",
            size_bytes=0,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=1,
            code_hash=code_hash,
        )
        result = CacheRatiosResultDTO(
            company_name=company_name,
            cache_key=entry.cache_key,
            hit=False,
            entry=entry,
        )
        return pd.DataFrame({"company": [company_name]}), result


class SequentialWorkerPool:
    def __init__(self) -> None:
        self.processed_tasks: list[tuple[int, dict]] = []

    def __call__(
        self,
        *,
        logger,
        tasks,
        processor,
        on_result,
        post_callback,
        max_workers,
        total_size,
    ):
        del logger, post_callback, max_workers
        tasks_list = list(tasks)
        self.processed_tasks.extend(tasks_list)
        for index, data in tasks_list:
            task = WorkerTaskDTO(
                index=index,
                data=data,
                worker_id="worker",
                total_size=total_size,
            )
            result = processor(task)
            if callable(on_result):
                on_result(result)
        return []


@pytest.fixture()
def config(tmp_path):
    db_path = tmp_path / "eligible_companies.db"
    return SimpleNamespace(
        database=SimpleNamespace(connection_string=f"sqlite:///{db_path}"),
        worker_pool=SimpleNamespace(max_workers=1),
        repository=SimpleNamespace(batch_size=50, persistence_threshold=1),
        fly_settings=SimpleNamespace(app_name="test-app", version="1"),
    )


def test_normalize_pipeline_reads_projection(config):
    logger = DummyLogger()

    eligible_repo = RepositoryCompanyEligible(config=config, logger=logger)
    uow_factory = UowFactory(session_factory=eligible_repo.Session)

    companies = [
        CompanyDataDTO(
            company_name="ACME SA",
            cvm_code="12345",
            ticker_codes=["ACME3"],
            trading_name="ACME",
            industry_sector="Sector",
            industry_subsector="Subsector",
            industry_segment="Segment",
            company_segment="Segment",
        )
    ]

    statements = [
        StatementFetchedDTO(
            nsd="1",
            company_name="ACME SA",
            quarter=datetime(2023, 12, 31),
            version="1",
            grupo="DFs Consolidadas",
            quadro="Balanço",
            account="ACC",
            description="Account",
            value=100.0,
        )
    ]

    quotes = [
        StockQuoteDTO(
            company_name="ACME SA",
            ticker="ACME3",
            date=datetime(2023, 12, 15),
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            adj_close=10.5,
            volume=1_000,
            currency="BRL",
        )
    ]

    company_repo = InMemoryCompanyRepository(companies)
    statement_repo = InMemoryStatementRepository(statements)
    quote_repo = InMemoryStockQuoteRepository(quotes)
    indicator_repo = DummyIndicatorsRepository()

    batch_service = EligibleCompaniesBatchUpdaterService(
        logger=logger,
        port=eligible_repo,
    )

    update_usecase = CompaniesEligibleUseCase(
        logger=logger,
        repository_company=company_repo,
        repository_statements_fetched=statement_repo,
        repository_stock_quote=quote_repo,
        batch_service=batch_service,
        uow_factory=uow_factory,
    )

    projection = update_usecase()
    assert len(projection) == 1
    assert projection[0].ticker_codes == ("ACME3",)

    companies_df = pd.DataFrame([company.to_dict() for company in projection])

    normalize_usecase = NormalizeUseCase(
        config=config,
        logger=logger,
        repository_stock_quote=quote_repo,
        repository_indicators=indicator_repo,
        repository_statements_fetched=statement_repo,
        cache_ratios=DummyCacheRatiosPort(),
        companies_eligible_port=eligible_repo,
        uow_factory=uow_factory,
        worker_pool=SequentialWorkerPool(),
    )
    fake_cache = FakeCacheRatiosService()
    normalize_usecase.cache_ratios_service = fake_cache
    normalize_usecase._ratios_code_hash = "fake-code"

    sample_statements = pd.DataFrame(
        {
            "quarter": [pd.Timestamp("2023-12-31")],
            "account": ["ACC"],
            "value": [100.0],
        }
    )
    sample_quotes = {
        "stock_1": pd.DataFrame(
            {
                "date": [pd.Timestamp("2023-12-15")],
                "close": [10.5],
            }
        )
    }

    def _mock_load_quotes(self, *, ticker_codes, uow):  # noqa: ANN001, ARG001
        return sample_quotes

    def _mock_load_statements(self, *, company_name, uow):  # noqa: ANN001, ARG001
        return {"statements": sample_statements}

    def _mock_treat_data(self, data, aggregate_method="last"):  # noqa: ANN001
        return {
            "quotes": data.get("quotes", {}),
            "statements": data.get("statements", {}),
            "indicators": data.get("indicators", {}),
        }

    def _mock_create_ratios(self, company_data):  # noqa: ANN001
        return pd.DataFrame({
            "company": [projection[0].company_name],
            "value": [42.0],
        })

    normalize_usecase._load_quotes = _mock_load_quotes.__get__(normalize_usecase, NormalizeUseCase)
    normalize_usecase._load_statements = _mock_load_statements.__get__(normalize_usecase, NormalizeUseCase)
    normalize_usecase._treat_data = _mock_treat_data.__get__(normalize_usecase, NormalizeUseCase)
    normalize_usecase._create_ratios = _mock_create_ratios.__get__(normalize_usecase, NormalizeUseCase)

    results = normalize_usecase.run(companies=companies_df)

    assert len(results.items) == 1
    assert fake_cache.calls == ["ACME SA"]
