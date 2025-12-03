from datetime import datetime, timedelta
from typing import Any, List

from dateutil.relativedelta import relativedelta

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort
from infrastructure.utils.list_flatenner import ListFlattener

# from infrastructure.helpers.list_flattener import ListFlattener


class SyncStockQuoteUseCase:
    """Use case for synchronizing data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        scraper_stock_quote: ScraperStockQuotePort,

        uow_factory: UowFactoryPort,

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

        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Run the full synchronization pipeline.

        Steps:
            1. Retrieve company data from the scraper.
            2. Transform results into ``CompanyDataDTO`` objects.
            3. Save them into the repository in batches.

        Returns:
            SyncCompanyDataResultDTO: Summary of the synchronization process,
            including counts and network usage metrics.
        """
        # Collect company identifiers already stored in the repository
        with self.uow_factory() as uow:
            results: list[StockQuoteDTO] = []
            try:
                # existing_codes = [code for (code,) in self.repository_company.iter_existing_by_columns("company_name", uow=uow)]

                columns = ["company_name", "ticker_codes", "isin_codes"]
                codes = [code for (code,) in self.repository_company.iter_existing_by_columns(columns, uow=uow)]

                seen = set()
                company_codes: List[tuple[str, str]] = [
                    (t, name)
                    for name, tickers, _ in codes
                    for t in (s.strip() for s in str(tickers or "").replace(" ", "").split(","))
                    if t and not (t in seen or seen.add(t))
                ]

                # anexa a última data persistida por ticker
                existing_codes: list[tuple[str, str, datetime | None, datetime]] = []
                today = datetime.today()
                for t, n in company_codes:
                    last_date = self.repository_stock_quote.get_last_date(ticker=t, uow=uow)
                    if last_date is None:
                        start_date = today - relativedelta(years=99)
                    else:
                        # se o repositório retorna date, combine com meia-noite
                        if isinstance(last_date, datetime):
                            start_date = last_date + timedelta(days=1)
                        else:
                            start_date = datetime.combine(last_date, datetime.min.time()) + timedelta(days=1)

                    existing_codes.append((t, n, start_date, today))

                # Fetch companies from scraper and persist them in batch mode
                results = self.scraper_stock_quote.fetch_all(existing_codes=existing_codes, save_callback=self._save_batch)

            except Exception as e:
                self.logger.log(f"{e}", level="error")

            return SyncResultsDTO(items=results, metrics=self.scraper_stock_quote.get_metrics())

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
        self.repository_stock_quote.save_all(dtos, uow=uow)

    # def _get_tickers(self, uow) -> list[tuple[str, str]]:
    #     columns = ["company_name", "ticker_codes", "isin_codes"]

    #     pairs: list[tuple[str, str]] = []
    #     for row in self.repository_company.iter_existing_by_columns(columns, include_nulls=False, uow=uow):
    #         # alguns drivers retornam ((a,b,c),)
    #         if isinstance(row, tuple) and len(row) == 1 and hasattr(row[0], "_mapping"):
    #                 row = row[0]

    #         company_name, ticker_codes, isin_codes = row

    #         # include_nulls=False makes this reduntant, but just in case
    #         isins = [s.strip() for s in str(isin_codes or "").split(",") if s.strip()]
    #         if not isins:
    #             continue  # ignora empresas sem ISIN

    #         tickers = [t.strip() for t in str(ticker_codes or "").replace(" ", "").split(",") if t.strip()]
    #         for t in tickers:
    #             pairs.append((t, company_name))
    #     return pairs


# from datetime import date, timedelta
# from dateutil.relativedelta import relativedelta
# from typing import Any, Iterable, Iterator, List

# from application.ports.config_port import ConfigPort
# from application.ports.logger_port import LoggerPort
# from application.ports.uow_port import Uow, UowFactoryPort
# from application.ports.http_client_port import AffinityHttpClientPort
# from domain.dtos.stock_quote_dto import StockQuoteDTO
# from domain.dtos.sync_results_dto import SyncResultsDTO
# from domain.dtos.worker_task_dto import WorkerTaskDTO
# from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
# from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
# from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort
# from infrastructure.utils.list_flatenner import ListFlattener

# # from infrastructure.helpers.list_flattener import ListFlattener
# from infrastructure.utils.save_strategy import SaveStrategy


# class SyncStockQuoteUseCase:
#     """Use case for synchronizing company data between scraper and repository."""

#     def __init__(
#         self,
#         config: ConfigPort,
#         logger: LoggerPort,

#         repository_company: RepositoryCompanyDataPort,
#         repository_stock_quote: RepositoryStockQuotePort,
#         scraper_stock_quote: ScraperStockQuotePort,

#         uow_factory: UowFactoryPort,

#         max_workers: int = 1,
#     ):
#         """Initialize the use case with its dependencies.

#         Args:
#             config (ConfigPort): Application configuration provider.
#             logger (LoggerPort): Logger interface for capturing messages.
#             repository (RepositoryCompanyDataPort): Repository for persisting company data.
#             scraper (ScraperCompanyDataPort): Scraper used to fetch company data.
#             max_workers (int, optional): Maximum number of workers for parallel execution.
#                 Defaults to 1, or falls back to the value in the config worker pool.
#         """
#         self.config = config
#         self.logger = logger
#         self.repository_company = repository_company
#         self.repository_stock_quote = repository_stock_quote
#         self.scraper_stock_quote = scraper_stock_quote
#         self.uow_factory = uow_factory

#         self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

#     def __call__(self, task: WorkerTaskDTO) -> Any:
#         return self.run(task)

#     def run(self, task: WorkerTaskDTO) -> SyncResultsDTO[StockQuoteDTO]:
#         """
#         """
#         ticker, company_name = task.data
#         today = date.today()

#         items: list[StockQuoteDTO] = []

#         with self.uow_factory() as uow:
#             # get ticker last date
#             last_date = self.repository_stock_quote.get_last_date(ticker=ticker, uow=uow)
#             start_date = (today - relativedelta(years=99)) if last_date is None else (last_date + timedelta(days=1))
#             if start_date > today:
#                 t = today
#                 today = start_date
#                 start_date = t

#             strategy = SaveStrategy.from_config(
#                 save_callback=self._save_batch,
#                 threshold=self.config.repository.persistence_threshold,
#                 config=self.config,
#                 uow_factory=self.uow_factory,
#             )

#             # wrapper para casar a assinatura do Scraper (items, *, uow)
#             def _strategy_callback(
#                 batch: list[StockQuoteDTO],
#                 *,
#                 uow: Uow | None = None,
#             ) -> None:
# # <<<<<<< codex/adjust-stock_quote-pipeline-logic-4v8pke
#                 # Considera cada símbolo/ticker como um único item na estratégia,
#                 # permitindo que o threshold seja aplicado por ticker (como no fluxo
#                 # de companies) em vez de por quantidade de DTOs individuais.
#                 strategy.handle(batch)
# # =======
# #                 strategy.handle_many(batch)  # não recebe uow; wrapper satisfaz a assinatura
# # >>>>>>> 2025-09-20-Stock-Value

#             items = self.scraper_stock_quote.fetch_all(
#                 save_callback=_strategy_callback,
#                 data=task.data,
#                 start_date=start_date,
#                 end_date=today,
#                 uow=uow,
#                 http_client=self.http_client,
#             )
#         strategy.finalize()

#         return SyncResultsDTO(items=items, metrics=len(items))

#     def stream_codes(self, codes: Iterable[int]) -> Iterator[int]:
#         """Gerador preguiçoso sobre a lista já calculada externamente."""
#         for code in codes:
#             yield code

#     def _save_batch(
#         self,
#         items: list[StockQuoteDTO] | list[list[StockQuoteDTO]],
#         *,
#         uow: Uow | None = None,
#     ) -> None:
#         """Transform and persist a batch of company data.

#         Args:
#             buffer (List[CompanyDataDTO]): Raw or nested DTOs retrieved by the scraper.
#         """
#         # type narrowing
#         if uow is None:
#             raise RuntimeError("SaveCallback chamado sem UoW")

#         # with self.uow_factory() as uow:
#         # Flatten potential nested lists from scraper output (lista por ticker)
#         flat_items = ListFlattener.flatten(items)

#         # Convert raw scraper DTOs into domain-level DTOs
#         dtos = [StockQuoteDTO.from_raw(item) for item in flat_items]


#         # Persist the transformed DTOs in bulk
#         self.repository_stock_quote.save_all(dtos, uow=uow)
