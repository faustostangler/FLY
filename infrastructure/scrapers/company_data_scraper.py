from __future__ import annotations

import base64
import json
import time
from typing import Callable, Dict, List, Optional, TypeVar

from application.mappers.company_data_mapper import CompanyDataMapper

from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO

from domain.ports.http_client_port import AffinityHttpClientPort
from domain.ports.scraper_company_data_port import CompanyDataScraperPort
from domain.ports.config_port import ConfigPort
from domain.ports.datacleaner_port import DataCleanerPort
from domain.ports.logger_port import LoggerPort
from domain.ports.metrics_collector_port import MetricsCollectorPort
from domain.ports.worker_pool_port import WorkerPoolPort

# from infrastructure.scrapers.company_data_processors import (
#     CompanyDataDetailProcessor,
#     CompanyDataMerger,
#     DetailFetcher,
#     EntryCleaner,
# )
from infrastructure.utils import ByteFormatter
from infrastructure.utils.save_strategy import SaveStrategy

T = TypeVar("T")


class CompanyDataScraper(CompanyDataScraperPort):
    """Scraper adapter responsible for fetching raw company data.

    In a real implementation, this could use requests, BeautifulSoup, or
    Selenium.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        datacleaner: DataCleanerPort,
        mapper: CompanyDataMapper,
        metrics_collector: MetricsCollectorPort,
        worker_pool: WorkerPoolPort,
        http_client: AffinityHttpClientPort,
    ):
        # hardcoded parameters
        self.PAGE_NUMBER = 1
        self.PAGE_SIZE = 120

        # Store configuration and logger for use throughout the scraper
        self.config = config
        self.logger = logger
        self.data_cleaner = datacleaner
        self.mapper = mapper
        self.worker_pool_executor = worker_pool
        self._metrics_collector = metrics_collector

        # Shared HTTP client providing connection reuse, limiter and cache
        self.http_client = http_client

        # Set language and API company_data_endpoint from configuration
        self.language = self.config.exchange.language
        self.endpoint_companies_list = config.exchange.company_data_endpoint["initial"]
        self.endpoint_detail = config.exchange.company_data_endpoint["detail"]
        self.endpoint_financial = config.exchange.company_data_endpoint["financial"]

        self.byte_formatter = ByteFormatter()

        from application.mappers.company_data_merger import CompanyDataMerger
        from application.processors.entry_cleaner import EntryCleaner
        from infrastructure.scrapers.company_detail_scraper import DetailFetcher
        

        self.company_data_merger = CompanyDataMerger(self.mapper, self.logger)
        self.entry_cleaner = EntryCleaner(self.data_cleaner)
        self.detail_fetcher = DetailFetcher(http_client=self.http_client, endpoint_detail=self.endpoint_detail, language=self.language)
        self.detail_processor = CompanyDataDetailProcessor(cleaner=self.entry_cleaner, fetcher=self.detail_fetcher, merger=self.company_data_merger)

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        skip_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[CompanyDataDTO]], None]] = None,
        **kwargs,
    ) -> List[CompanyDataDTO]:
        # Ensure skip_codes is a set (to avoid None and allow fast lookup)
        self.skip_codes = skip_codes or set()
        # Determine the save threshold (number of companies before saving buffer)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50
        # Determine the number of simultaneous process

        def noop(_buffer: List[Dict]) -> None:
            return None

        # 1 Fetch the initial list of companies, possibly skipping some CVM codes
        companies_list = self._fetch_companies_list(save_callback=noop)

        # 2 Fetch and parse detailed information for each company, with optional skipping and periodic saving
        companies = self._fetch_companies_details(companies_list=companies_list.items, save_callback=save_callback)

        # Return the complete list of parsed company details
        return companies

    def _fetch_companies_list(
        self,
        save_callback: Optional[Callable[[List[Dict]], None]] = None,
    ) -> List[CompanyDataDTO]:
        """Busca o conjunto inicial de empresas disponíveis na bolsa.

        :return: Lista de empresas com código CVM e nome base.
        """
        # self.logger.log("Run  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_list(save_callback, max_workers, threshold)", level="info")

        strategy: SaveStrategy[Dict] = SaveStrategy.from_config(
            save_callback, self.threshold, config=self.config
        )
        results = []

        # hardcoded first page
        page = 1

        download_bytes_pre = self._metrics_collector.network_bytes
        fetch = self._fetch_page(page)
        download_bytes_pos = self._metrics_collector.network_bytes - download_bytes_pre

        total_pages = fetch.total_pages

        results = list(fetch.items)
        for item in fetch.items:
            strategy.handle(item)

        extra_info = {
            "Download": self.byte_formatter.format_bytes(download_bytes_pos),
            "Total download": self.byte_formatter.format_bytes(
                self.metrics_collector.network_bytes
            ),
        }
        self.logger.log(
            f"Page {page}/{total_pages}",
            level="info",
            progress={
                "index": 0,
                "size": total_pages,
                "start_time": start_time,
            },
            extra=extra_info,
        )

        if total_pages > 1:
            tasks = list(enumerate(range(2, total_pages + 1)))

            def processor(task: WorkerTaskDTO) -> PageResultDTO:
                # self.logger.log("Run  Method CompanyDataScraper._fetch_companies_list().processor()", level="info")
                download_bytes_pre = self._metrics_collector.network_bytes

                # self.logger.log("Call Method CompanyDataScraper._fetch_companies_list().processor()_fetch_page()", level="info")
                fetch = self._fetch_page(task.data)
                # self.logger.log("End  Method CompanyDataScraper._fetch_companies_list().processor()_fetch_page()", level="info")

                download_bytes_pos = (
                    self._metrics_collector.network_bytes - download_bytes_pre
                )

                extra_info = {
                    "Download": self.byte_formatter.format_bytes(download_bytes_pos),
                    "Total download": self.byte_formatter.format_bytes(
                        self.metrics_collector.network_bytes
                    ),
                }
                self.logger.log(
                    f"Page {task.data}/{total_pages}",
                    level="info",
                    progress={
                        "index": task.index + 1,
                        "size": total_pages,
                        "start_time": start_time,
                    },
                    extra=extra_info,
                    worker_id=task.worker_id,
                )

                # self.logger.log("End  Method CompanyDataScraper._fetch_companies_list().processor()", level="info")
                return fetch

            page_exec = self.worker_pool_executor.run(
                tasks=tasks,
                processor=processor,
                logger=self.logger,
            )

            # Merge and flush each fetched page
            for page_data in page_exec.items:
                results.extend(page_data.items)

        strategy.finalize()

        # self.logger.log(
        #     f"Global download: {self.byte_formatter.format_bytes(self.metrics_collector.network_bytes)}",
        #     level="info",
        # )

        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_list(save_callback, max_workers, threshold)", level="info")

        return List[CompanyDataDTO]

    def _fetch_companies_details(
        self,
        companies_list: List[Dict],
        save_callback: Optional[Callable[[List[CompanyDataDTO]], None]] = None,
    ) -> List[CompanyDataDTO]:
        """
        Fetches and parses detailed information for a list of companies, with optional skipping and periodic saving.
        Args:
            companies_list (List[Dict]): List of company dictionaries, each containing at least a "codeCVM" key.
            skip_codes (Optional[Set[str]], optional): Set of CVM codes to skip during processing. Defaults to None.
            save_callback (Optional[Callable[[List[CompanyDataRawDTO]], None]], optional):
                Callback function to save buffered company details periodically.
                Defaults to None.
            threshold (Optional[int], optional): Number of companies to process before triggering the save_callback. If not provided, uses configuration or defaults to 50.
            max_workers (int | None, optional): Reserved for future parallel fetching.
        Returns:
            ExecutionResultDTO[CompanyDataRawDTO]: Parsed company detail DTOs and
            execution metrics.
        Logs:
            - Progress and status information at each step.
            - Warnings for any exceptions encountered during processing.
        Raises:
            - Does not raise exceptions; logs warnings instead.
        """
        # self.logger.log("Run  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_details(save_callback, max_workers, threshold)", level="info")

        strategy: SaveStrategy[CompanyDataRawDTO] = SaveStrategy(
            save_callback, self.threshold, config=self.config
        )
        detail_exec: ExecutionResultDTO[Optional[CompanyDataRawDTO]] = (
            ExecutionResultDTO(items=[], metrics=self.metrics_collector.get_metrics(0))
        )

        # Pair each company dict with its index for progress logging
        tasks = list(enumerate(companies_list))
        start_time = time.perf_counter()

        def processor(task: WorkerTaskDTO) -> Optional[CompanyDataRawDTO]:
            # self.logger.log("Run  Method CompanyDataScraper._fetch_companies_details().processor()", level="info")
            index = task.index
            entry = task.data
            worker_id = task.worker_id

            company_name = self.data_cleaner.clean_text(entry.get("companyName"))
            if company_name in self.skip_codes:
                # download_bytes_pre = self._metrics_collector.network_bytes
                # download_bytes_pos = self._metrics_collector.network_bytes - download_bytes_pre

                # Log and skip already persisted companies
                extra_info = {
                    "issuingCompany": entry["issuingCompany"],
                    "trading_name": entry["tradingName"],
                    # "Download": self.byte_formatter.format_bytes(download_bytes_pos),
                    # "Total download": self.byte_formatter.format_bytes(self.metrics_collector.network_bytes),
                }
                self.logger.log(
                    f"{entry.get('codeCVM')}",
                    level="info",
                    progress={
                        "index": index,
                        "size": len(tasks),
                        "start_time": start_time,
                    },
                    extra=extra_info,
                    worker_id=worker_id,
                )

                return None

            download_bytes_pre = self._metrics_collector.network_bytes

            # self.logger.log("Call Method CompanyDataScraper._fetch_companies_details().processor().self.detail_processor.run(entry)", level="info")
            result = self.detail_processor.process_entry(entry)
            # self.logger.log("End  Method CompanyDataScraper._fetch_companies_details().processor().self.detail_processor.run(entry)", level="info")

            download_bytes_pos = (
                self._metrics_collector.network_bytes - download_bytes_pre
            )

            issuingCompany = entry.get("issuingCompany")
            tradingName = entry.get("tradingName")
            extra_info = {
                "issuingCompany": issuingCompany,
                "trading_name": tradingName,
                "Download": self.byte_formatter.format_bytes(download_bytes_pos),
                "Total download": self.byte_formatter.format_bytes(
                    self.metrics_collector.network_bytes
                ),
            }
            self.logger.log(
                f"{entry.get('codeCVM')}",
                level="info",
                progress={
                    "index": index,
                    "size": len(tasks),
                    "start_time": start_time,
                },
                extra=extra_info,
                worker_id=worker_id,
            )

            # self.logger.log("End  Method CompanyDataScraper._fetch_companies_details().processor()", level="info")

            return result

        def handle_batch(item: Optional[CompanyDataRawDTO]) -> None:
            # Buffer each parsed company and flush when threshold is hit
            # self.logger.log("Call Method strategy.handle()", level="info")
            if item is not None:
                strategy.handle([item])
            # self.logger.log("End  Method strategy.handle()", level="info")

        detail_exec = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
        )
        # self.logger.log("Processor processed_entry results", level="info")

        strategy.finalize()

        results = [item for item in detail_exec.items if item is not None]

        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_details(save_callback, max_workers, threshold)", level="info")

        return ExecutionResultDTO(items=results, metrics=detail_exec.metrics)

    def _encode_payload(self, payload: dict) -> str:
        """Codifica um dicionário JSON para o formato base64 usado pela API.

        :param payload: Dicionário de entrada
        :return: String base64
        """

        return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    def _fetch_page(self, page_number: int) -> list[T]:
        # self.logger.log("Run  Method CompanyDataScraper._fetch_companies_list().processor()_fetch_page()", level="info")
        payload = {
            "language": self.language,
            "pageNumber": page_number,
            "pageSize": self.PAGE_SIZE,
        }
        token = self._encode_payload(payload)

        url = self.endpoint_companies_list + token
        with self.http_client.borrow_session() as session:
            body = self.http_client.fetch_with(session, url)

        self._metrics_collector.add_network_bytes(len(body))
        data = json.loads(body.decode("utf-8"))

        results = data.get("results", [])
        total_pages = data.get("page", {}).get("totalPages", 1)

        return results

    # @property
    # def metrics_collector(self) -> MetricsCollectorPort:
    #     """Metrics collector used by the scraper."""

    #     return self._metrics_collector
