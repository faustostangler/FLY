from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Iterable, Iterator, Sequence

import pytest

from application.services.eligible_companies_service import EligibleCompaniesService
from application.usecases.statements_sync import StatementsUseCase
from application.usecases.statements_transformer import StatementTransformer
from domain.dtos import (
    CacheRatiosEntryDTO,
    CacheRatiosResultDTO,
    CompanyDataDTO,
    CompanyEligibleDTO,
    NsdDTO,
    StatementFetchedDTO,
    StatementRawDTO,
    StatementsSyncItemDTO,
    SyncResultsDTO,
)
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.eligible_companies_command_dto import EligibleCompaniesCommandDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO
from domain.ports.eligible_companies_read_port import EligibleCompaniesReadPort
from domain.services.service_ratios import RatiosService
from infrastructure.repositories.eligible_companies_repository import (
    EligibleCompaniesReadRepository,
    EligibleCompaniesWriteRepository,
)
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.repositories.repository_nsd import RepositoryNsd
from infrastructure.repositories.repository_statements_fetched import (
    StatementFetchedRepository,
)
from infrastructure.repositories.repository_statements_raw import StatementRawRepository
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory
from presentation.controllers.cli import Cli


class DummyLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict]] = []

    def log(self, message: str, level: str = "info", **extra: object) -> None:  # noqa: D401
        self.records.append((message, level, extra))


class FakeUow:
    def __init__(self) -> None:
        self.session = object()
        self._committed = False

    def __enter__(self) -> "FakeUow":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        return None

    def commit(self) -> None:
        self._committed = True


class FakeUowFactory:
    def __call__(self) -> FakeUow:
        return FakeUow()


class SequentialWorkerPool:
    def __call__(
        self,
        *,
        logger,
        tasks: Iterable[tuple[int, object]],
        processor,
        on_result,
        post_callback,
        max_workers,
        total_size,
    ) -> Iterator[object]:
        del logger, post_callback, max_workers
        for index, data in tasks:
            result = processor(
                SimpleNamespace(
                    index=index,
                    data=data,
                    worker_id="worker",
                    total_size=total_size,
                )
            )
            if callable(on_result):
                on_result(result)
            yield result


class InMemoryEligibleReadPort(EligibleCompaniesReadPort):
    def __init__(self, companies: Sequence[CompanyEligibleDTO], version: str) -> None:
        self._companies = list(companies)
        self._version = version

    def get_current(self, *, uow) -> EligibleCompaniesResultDTO | None:  # noqa: ANN001
        del uow
        if not self._companies:
            return None
        return EligibleCompaniesResultDTO(
            evaluated_count=len(self._companies),
            eligible_count=len(self._companies),
            version=self._version,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def list_current_companies(self, *, uow) -> list[CompanyEligibleDTO]:  # noqa: ANN001
        del uow
        return list(self._companies)

    def get_by_company_name(
        self,
        company_name: str,
        *,
        uow,
    ) -> CompanyEligibleDTO | None:  # noqa: ANN001
        del uow
        for company in self._companies:
            if company.company_name == company_name:
                return company
        return None


class DummyCachePort:
    def __init__(self) -> None:
        self.initialized = False
        self.stored: list[CacheRatiosEntryDTO] = []
        self.invalidated: list[str] = []

    def initialize(self) -> None:
        self.initialized = True

    def load(self, cache_key: str):  # noqa: D401
        return None

    def store(self, *, context, df, company_name: str) -> CacheRatiosEntryDTO:  # noqa: ANN001, D401
        del df, company_name
        entry = CacheRatiosEntryDTO(
            cache_key=context.cache_key,
            file_path="/tmp/cache",
            size_bytes=128,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=1,
            code_hash=context.code_hash,
        )
        self.stored.append(entry)
        return entry

    def invalidate_outdated(self, *, code_hash: str) -> None:
        self.invalidated.append(code_hash)


class InMemoryStatementRawRepository:
    def __init__(self, statements: Sequence[StatementRawDTO]) -> None:
        self._statements = list(statements)

    def get_all(self, *, uow, batch_size=None) -> list[StatementRawDTO]:  # noqa: ANN001, ARG002
        return list(self._statements)


class InMemoryStatementFetchedRepository:
    def __init__(self) -> None:
        self.items: list[StatementFetchedDTO] = []

    def save_all(self, items: Sequence[StatementFetchedDTO], *, uow) -> None:  # noqa: ANN001, ARG002
        self.items.extend(items)

    def get_all(self, *, uow, batch_size=None) -> list[StatementFetchedDTO]:  # noqa: ANN001, ARG002
        return list(self.items)


@pytest.fixture()
def config(tmp_path) -> SimpleNamespace:
    db_path = tmp_path / "fly.db"
    cache_path = tmp_path / "cache.db"
    return SimpleNamespace(
        database=SimpleNamespace(
            connection_string=f"sqlite:///{db_path}",
            connection_cache_string=f"sqlite:///{cache_path}",
        ),
        worker_pool=SimpleNamespace(max_workers=1),
        repository=SimpleNamespace(batch_size=50, persistence_threshold=1),
        domain=SimpleNamespace(
            recency_year=2020,
            statements_types=(),
            words_to_remove=(),
        ),
        cache=SimpleNamespace(
            parquet_compression="snappy",
            max_age=SimpleNamespace(days=30),
            max_cache_size_bytes=10_000_000,
        ),
        fly_settings=SimpleNamespace(version="test"),
    )


def test_statements_use_case_transforms_and_persists(config):
    logger = DummyLogger()
    raw_rows = [
        StatementRawDTO(
            id=None,
            nsd="1",
            company_name="ACME SA",
            quarter="2023-03-31",
            version="1",
            grupo="DFs Consolidadas",
            quadro="Quadro",
            account="RECEITAS",
            description="Receita líquida",
            value=1000.0,
        )
    ]
    raw_repo = InMemoryStatementRawRepository(raw_rows)
    fetched_repo = InMemoryStatementFetchedRepository()
    uow_factory = FakeUowFactory()

    transformer = StatementTransformer(cleaner=SimpleNamespace(clean_text=lambda x: x))
    use_case = StatementsUseCase(
        logger=logger,
        repository_statements_raw=raw_repo,
        repository_statements_fetched=fetched_repo,
        transformer=transformer,
        uow_factory=uow_factory,
    )

    result = use_case.run()

    assert result.metrics == len(raw_rows)
    assert any(item.source == "raw" for item in result.items)
    assert len(fetched_repo.items) == len(raw_rows)


def test_eligible_companies_service_persists_projection_and_idempotent(config):
    logger = DummyLogger()
    company_repo = RepositoryCompanyData(config=config, logger=logger)
    nsd_repo = RepositoryNsd(config=config, logger=logger)
    fetched_repo = StatementFetchedRepository(config=config, logger=logger)
    stock_repo = RepositoryStockQuote(config=config, logger=logger)
    read_repo = EligibleCompaniesReadRepository(config=config, logger=logger)
    write_repo = EligibleCompaniesWriteRepository(config=config, logger=logger)
    uow_factory = UowFactory(session_factory=company_repo.Session)

    company = CompanyDataDTO(
        id=None,
        company_name="ACME SA",
        cvm_code="123",
        ticker_codes=("ACME3",),
    )
    statement = StatementFetchedDTO(
        id=None,
        nsd="1",
        company_name="ACME SA",
        quarter="2023-03-31",
        version="1",
        grupo="DFs Consolidadas",
        quadro="Quadro",
        account="Receita",
        description="Receita",
        value=10.0,
    )
    quote = StockQuoteDTO(
        id=None,
        company_name="ACME SA",
        ticker="ACME3",
        date="2023-03-31",
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        adj_close=1.0,
        volume=1,
        currency="BRL",
    )
    nsd = NsdDTO(
        nsd=1,
        company_name="ACME SA",
        quarter=datetime(2023, 3, 31),
        version=1,
        nsd_type=None,
        dri=None,
        auditor=None,
        responsible_auditor=None,
        protocol=None,
        sent_date=datetime(2023, 4, 1),
        reason=None,
    )

    with uow_factory() as uow:
        company_repo.save_all([company], uow=uow)
        nsd_repo.save_all([nsd], uow=uow)
        fetched_repo.save_all([statement], uow=uow)
        stock_repo.save_all([quote], uow=uow)
        uow.commit()

    service = EligibleCompaniesService(
        logger=logger,
        repository_company=company_repo,
        repository_statements_fetched=fetched_repo,
        repository_stock_quote=stock_repo,
        read_port=read_repo,
        write_port=write_repo,
        uow_factory=uow_factory,
    )

    command = EligibleCompaniesCommandDTO(version="v1")
    result = service.run(command)

    assert result.eligible_count == 1

    second = service.run(command)
    assert second.version == result.version
    with uow_factory() as uow:
        projection = read_repo.list_current_companies(uow=uow)
    assert len(projection) == 1


def test_ratios_service_uses_projection_and_invalidates_cache():
    logger = DummyLogger()
    cache_port = DummyCachePort()
    worker_pool = SequentialWorkerPool()
    eligible_company = CompanyEligibleDTO(
        company_name="ACME SA",
        ticker_codes=("ACME3",),
        projection_version="v2",
    )
    eligible_port = InMemoryEligibleReadPort([eligible_company], version="v2")
    config = SimpleNamespace(worker_pool=SimpleNamespace(max_workers=1))

    class DummyNormalizeUseCase:
        def __init__(self, cache: DummyCachePort) -> None:
            self.cache = cache

        def run(self) -> SyncResultsDTO[CacheRatiosResultDTO]:
            entry = CacheRatiosEntryDTO(
                cache_key="acme",  # type: ignore[arg-type]
                file_path="/tmp/cache",
                size_bytes=128,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=1,
                code_hash="dummy",
            )
            self.cache.stored.append(entry)
            self.cache.invalidated.append("dummy")
            result = CacheRatiosResultDTO(
                company_name="ACME SA",
                cache_key=entry.cache_key,
                hit=False,
                entry=entry,
            )
            return SyncResultsDTO(items=[result], metrics=entry.size_bytes)

        __call__ = run

    ratios_service = RatiosService(
        config=config,
        logger=logger,
        repository_stock_quote=SimpleNamespace(),
        repository_indicators=SimpleNamespace(),
        repository_statements_fetched=SimpleNamespace(),
        cache_ratios=cache_port,
        uow_factory=FakeUowFactory(),
        worker_pool=worker_pool,
        eligible_companies_read_port=eligible_port,
    )
    ratios_service.normalize_usecase = DummyNormalizeUseCase(cache_port)

    result = ratios_service.run()

    assert cache_port.stored, "Expected cache entries to be written"
    assert cache_port.invalidated, "Expected cache invalidation to run"
    assert len(result.items) == len(cache_port.stored)


def test_cli_runs_phases_in_order(config):
    logger = DummyLogger()
    order: list[str] = []

    class StubStatements:
        def run(self) -> SyncResultsDTO[StatementsSyncItemDTO]:
            order.append("statements")
            return SyncResultsDTO(
                items=[StatementsSyncItemDTO(source="raw", count=1)],
                metrics=0,
            )

    class StubEligible:
        def run(self, cmd: EligibleCompaniesCommandDTO) -> EligibleCompaniesResultDTO:
            order.append("eligible")
            return EligibleCompaniesResultDTO(
                evaluated_count=1,
                eligible_count=1,
                version=cmd.version,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

    class StubRatios:
        def run(self) -> SyncResultsDTO[CacheRatiosResultDTO]:
            order.append("ratios")
            return SyncResultsDTO(items=[], metrics=0)

    cli = Cli(
        config=config,
        logger=logger,
        statements_use_case=StubStatements(),
        eligible_companies_service=StubEligible(),
        ratios_service=StubRatios(),
    )

    cli.run()

    assert order == ["statements", "eligible", "ratios"]


def test_cli_short_circuits_ratios_when_no_eligible(config):
    logger = DummyLogger()
    order: list[str] = []

    class StubStatements:
        def run(self) -> SyncResultsDTO[StatementsSyncItemDTO]:
            order.append("statements")
            return SyncResultsDTO(items=[], metrics=0)

    class StubEligible:
        def run(self, cmd: EligibleCompaniesCommandDTO) -> EligibleCompaniesResultDTO:
            order.append("eligible")
            return EligibleCompaniesResultDTO(
                evaluated_count=0,
                eligible_count=0,
                version=cmd.version,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

    class StubRatios:
        def run(self) -> SyncResultsDTO[CacheRatiosResultDTO]:
            pytest.fail("Ratios phase should be skipped when there are no eligible companies")

    cli = Cli(
        config=config,
        logger=logger,
        statements_use_case=StubStatements(),
        eligible_companies_service=StubEligible(),
        ratios_service=StubRatios(),
    )

    cli.run()

    assert order == ["statements", "eligible"]
    assert any(
        message == "Eligible companies projection is empty; skipping ratios phase"
        for message, _, _ in logger.records
    )
