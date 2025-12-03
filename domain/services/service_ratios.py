from typing import Any, List, Dict, Optional
import pandas as pd


from application.processors.filter_builder import FilterBuilder
from infrastructure.utils.pandas_visitor import PandasVisitor
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from application.usecases.normalize_ratios import NormalizeUseCase
from application.usecases.companies_eligible import (
    CompaniesEligibleUseCase,
)
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.dtos import CacheRatiosResultDTO, SyncResultsDTO
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.value_objects import SearchFilterTree


class RatiosService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        cache_ratios: CacheRatiosPort,

        uow_factory: UowFactoryPort,
        worker_pool: WorkerPoolPort,
        companies_eligible_port: CompaniesEligiblePort,
    ):
        """Initialize the service with required dependencies.

        Args:
            config (ConfigPort): Provides application configuration settings.
            logger (LoggerPort): Logging interface for tracking operations.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper for fetching company data.
        """
        # Keep references to injected dependencies
        self.logger = logger
        self.config = config

        self.repository_company = repository_company
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_fetched = repository_statements_fetched
        self.cache_ratios = cache_ratios
        self.companies_eligible_port = companies_eligible_port

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool
        # self.http_client = http_client

        self._companies_eligible_batch_service = EligibleCompaniesBatchUpdaterService(
            logger=self.logger,
            port=companies_eligible_port,
        )

        self.companies_eligible_usecase = CompaniesEligibleUseCase(
            logger=self.logger,
            repository_company=self.repository_company,
            repository_statements_fetched=self.repository_statements_fetched,
            repository_stock_quote=self.repository_stock_quote,
            batch_service=self._companies_eligible_batch_service,
            uow_factory=self.uow_factory,
        )

        # Initialize the use case responsible for company synchronization
        self.normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,

            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            cache_ratios=self.cache_ratios,
            companies_eligible_port=companies_eligible_port,

            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO[CacheRatiosResultDTO]:
        return self.run(filters=kwds.get("filters"))

    def run(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResultsDTO[CacheRatiosResultDTO]:
        """
        Executa a normalização com filtros complexos.

        Args:
        """
        filter_tree = SearchFilterTree.from_raw(filters)

        with self.uow_factory() as uow:
            companies_eligible: List[CompanyEligibleDTO] = self.companies_eligible_port.list(uow=uow)

        df = pd.DataFrame([c.to_dict() for c in companies_eligible])

        companies_to_process = self._apply_filters(df, filter_tree)
        if companies_to_process.empty:
            return SyncResultsDTO(items=[], metrics=0)

        return self.normalize_usecase(companies=companies_to_process)

    def _apply_filters(
        self,
        df: pd.DataFrame,
        filters: Optional[SearchFilterTree],
    ) -> pd.DataFrame:
        if filters is None or filters.is_empty():
            return df
        try:
            spec = FilterBuilder().build_spec(filters.to_dict())
            mask = spec.accept(PandasVisitor(), df)
            return df[mask]
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    "Falha ao aplicar filtros em RatiosService: %s",
                    e,
                )
            return df

