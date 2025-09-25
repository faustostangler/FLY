from datetime import date, timedelta
from typing import Any, Iterable, Iterator

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from application.ports.http_client_port import AffinityHttpClientPort
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort
from infrastructure.utils.list_flatenner import ListFlattener

# from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.utils.save_strategy import SaveStrategy


class SyncStockQuoteUseCase:
    """Use case for synchronizing company data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        scraper_stock_quote: ScraperStockQuotePort,
        uow_factory: UowFactoryPort,
        http_client: AffinityHttpClientPort,

        max_workers: int = 1,
    ):
        """Initialize the use case with its dependencies.

        Args:
            config (ConfigPort): Application configuration provider.
            logger (LoggerPort): Logger interface for capturing messages.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper used to fetch company data.
            max_workers (int, optional): Maximum number of workers for parallel execution.
                Defaults to 1, or falls back to the value in the config worker pool.
        """
        self.config = config
        self.logger = logger
        self.repository_company = repository_company
        self.repository_stock_quote = repository_stock_quote
        self.scraper_stock_quote = scraper_stock_quote
        self.uow_factory = uow_factory
        self.http_client = http_client

        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def __call__(self, task: WorkerTaskDTO) -> Any:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> SyncResultsDTO[StockQuoteDTO]:
        """
        """
        ticker, company_name = task.data


        today = date.today()
        saved = 0

        with self.uow_factory() as uow:
            try:
                # get ticker last date
                last = self.repository_stock_quote.get_last_date(ticker=ticker, uow=uow)
                start_date = date(1900, 1, 1) if last is None else (last + timedelta(days=1))
                if start_date and start_date > today:
                    self.logger.log(f"Algouma coisa errada com a data", level="warning")
                    return SyncResultsDTO(items_count=0, extra={"ticker": ticker})
                
                items = self.scraper_stock_quote.fetch_all(
                    threshold=self.config.repository.persistence_threshold,
                    existing_codes=None,
                    save_callback=self._save_batch,
                    data=task.data,
                    start_date=start_date,
                    end_date=today,
                    uow=uow,
                    http_client=self.http_client,
                )


            except Exception as e:
                pass

        return SyncResultsDTO(items=(ticker, company_name), metrics=self.scraper.get_metrics())

    def stream_codes(self, codes: Iterable[int]) -> Iterator[int]:
        """Gerador preguiçoso sobre a lista já calculada externamente."""
        for code in codes:
            yield code

    def _save_batch(
        self,
        items: list[StockQuoteDTO],
        *,
        uow: Uow | None = None,
    ) -> None:
        """Transform and persist a batch of company data.

        Args:
            buffer (List[CompanyDataDTO]): Raw or nested DTOs retrieved by the scraper.
        """
        # type narrowing
        if uow is None:
            raise RuntimeError("SaveCallback chamado sem UoW")

        # with self.uow_factory() as uow:
        # Flatten potential nested lists from scraper output
        flat_items = ListFlattener.flatten(items)

        # Convert raw scraper DTOs into domain-level DTOs
        dtos = [StockQuoteDTO.from_raw(item) for item in flat_items]


        # Persist the transformed DTOs in bulk
        self.repository.save_all(dtos, uow=uow)
