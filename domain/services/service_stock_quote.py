from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.usecases.sync_stock_quote import SyncStockQuoteUseCase
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort


class StockQuoteService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        scraper_stock_quote: ScraperStockQuotePort,

        uow_factory: UowFactoryPort,
        # http_client: AffinityHttpClientPort,
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
        self.scraper_stock_quote = scraper_stock_quote

        self.uow_factory = uow_factory
        # self.http_client = http_client

        # Initialize the use case responsible for company synchronization
        self.sync_stock_quote_usecase = SyncStockQuoteUseCase(
            config=self.config,
            logger=self.logger,

            repository_company=self.repository_company,
            repository_stock_quote=self.repository_stock_quote,
            scraper_stock_quote=self.scraper_stock_quote,

            uow_factory=self.uow_factory,
            # http_client=self.http_client,
            
            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO:
        return self.run()

    def run(self) -> SyncResultsDTO[StockQuoteDTO]:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        return self.sync_stock_quote_usecase()

        # with self.uow_factory() as uow:
        #     codes = self._get_tickers(uow)

        # code_stream = self.sync_stock_quote_usecase.stream_codes(codes)

        # results = self.worker_pool(
        #     logger=self.logger,
        #     tasks=enumerate(code_stream),
        #     processor=self.sync_stock_quote_usecase,
        #     total_size=len(codes)
        # )

        # items = list(results) if results is not None else []
        # return SyncResultsDTO[StockQuoteDTO](items=items, metrics=len(items))
        # # Delegate execution to the underlying use case
        # return self.sync_stock_quote_usecase()

