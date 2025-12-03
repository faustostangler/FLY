"""Scraper implementation for fetching company data from the stock exchange."""

from __future__ import annotations

import base64
import json
import time
from typing import Callable, Dict, List, Optional

from application import CompanyDataMapper
from domain.dto import (
    CompanyDataRawDTO,
    ExecutionResultDTO,
    PageResultDTO,
    WorkerTaskDTO,
)
from domain.ports import (
    ScraperCompanyDataPort,
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    WorkerPoolPort,
)
from infrastructure.helpers import SaveStrategy
from infrastructure.helpers.byte_formatter import ByteFormatter
from infrastructure.helpers.datacleaner import DataCleaner
from infrastructure.http.affinity_port import AffinityHttpClient
from infrastructure.scrapers.company_data_processors import (
    CompanyDataDetailProcessor,
    CompanyDataMerger,
    DetailFetcher,
    EntryCleaner,
)


class CompanyDataScraper(ScraperCompanyDataPort):
    """Scraper adapter responsible for fetching raw company data.

    In a real implementation, this could use requests, BeautifulSoup, or
    Selenium.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        datacleaner: DataCleaner,
        mapper: CompanyDataMapper,
        worker_pool_executor: WorkerPoolPort,
        metrics_collector: MetricsCollectorPort,
        http_client: AffinityHttpClient,
    ):
        """Set up configuration, logger and helper utilities for the scraper.

        Args:
            config (Config): Global configuration with exchange endpoints.
            logger (Logger): Logger used for progress and error messages.

        Attributes:
            config (Config): Stored configuration instance.
            logger (Logger): Stored logger instance.
            language (str): Language code for API requests.
            endpoint_companies_list (str): URL for the companies list endpoint.
            endpoint_detail (str): URL for the company detail endpoint.
            endpoint_financial (str): URL for the financial data endpoint.

        Returns:
            None
        """

        # hardcoded parameters
        self.PAGE_NUMBER = 1
        self.PAGE_SIZE = 120

        # Store configuration and logger for use throughout the scraper
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.mapper = mapper
        self.worker_pool_executor = worker_pool_executor
        self._metrics_collector = metrics_collector

        # Shared HTTP client providing connection reuse, limiter and cache
        self.http_client = http_client

        # Set language and API company_data_endpoint from configuration
        self.language = config.exchange.language
        self.endpoint_companies_list = config.exchange.company_data_endpoint["initial"]
        self.endpoint_detail = config.exchange.company_data_endpoint["detail"]
        self.endpoint_financial = config.exchange.company_data_endpoint["financial"]

        self.byte_formatter = ByteFormatter()

        # Initialize a counter for total processed items
        self.processed_count = 0

        self.entry_cleaner = EntryCleaner(self.datacleaner)
        self.detail_fetcher = DetailFetcher(
            http_client=self.http_client,
            endpoint_detail=self.endpoint_detail,
            language=self.language,
        )
        self.company_data_merger = CompanyDataMerger(self.mapper, self.logger)
        self.detail_processor = CompanyDataDetailProcessor(
            cleaner=self.entry_cleaner,
            fetcher=self.detail_fetcher,
            merger=self.company_data_merger,
        )

        # Log the initialization of the scraper
        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[CompanyDataRawDTO]], None]] = None,
        **kwargs,
    ) -> ExecutionResultDTO[CompanyDataRawDTO]:
        """Fetch all companies from the exchange.

        Args:
            threshold: Number of companies to buffer before saving.
            existing_codes: CVM codes to ignore.
            save_callback: Optional callback to persist partial results.
            max_workers: Optional thread count for future parallelism.

        Returns:
            List of dictionaries representing raw company data.
        """
        # self.logger.log("Run  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)", level="info")

        # Ensure existing_codes is a set (to avoid None and allow fast lookup)
        self.existing_codes = existing_codes or set()
        # Determine the save threshold (number of companies before saving buffer)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50
        # Determine the number of simultaneous process

        def noop(_buffer: List[Dict]) -> None:
            return None

        # 1 Fetch the initial list of companies, possibly skipping some CVM codes
        # self.logger.log("Call Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_list(save_callback, max_workers, threshold)", level="info")
        companies_list = self._fetch_companies_list(
            save_callback=noop,
        )
        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_list(save_callback, max_workers, threshold)", level="info")

        # 2 Fetch and parse detailed information for each company, with optional skipping and periodic saving
        # self.logger.log("Call Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_details(save_callback, max_workers, threshold)", level="info")
        companies = self._fetch_companies_details(
            companies_list=companies_list.items,
            save_callback=save_callback,
        )
        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_details(save_callback, max_workers, threshold)", level="info")

        # self.logger.log(
        #     f"Global download: {self.byte_formatter.format_bytes(self.metrics_collector.network_bytes)}",
        #     level="info",
        # )

        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)", level="info")

        # Return the complete list of fetched company details
        return companies

    def _fetch_companies_list(
        self,
        save_callback: Optional[Callable[[List[Dict]], None]] = None,
    ) -> ExecutionResultDTO[Dict]:
        """Busca o conjunto inicial de empresas disponíveis na bolsa.

        :return: Lista de empresas com código CVM e nome base.
        """
        # self.logger.log("Run  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)._fetch_companies_list(save_callback, max_workers, threshold)", level="info")

        strategy: SaveStrategy[Dict] = SaveStrategy(
            save_callback, self.threshold, config=self.config
        )
        page_exec = ExecutionResultDTO(
            items=[], metrics=self.metrics_collector.get_metrics(0)
        )
        fetch = PageResultDTO(items=[], total_pages=0, bytes_downloaded=0)
        results = []

        start_time = time.perf_counter()

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
                    worker_id=worker_id,
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

        return ExecutionResultDTO(items=results, metrics=page_exec.metrics)

    def _fetch_companies_details(
        self,
        companies_list: List[Dict],
        save_callback: Optional[Callable[[List[CompanyDataRawDTO]], None]] = None,
    ) -> ExecutionResultDTO[CompanyDataRawDTO]:
        """
        Fetches and parses detailed information for a list of companies, with optional skipping and periodic saving.
        Args:
            companies_list (List[Dict]): List of company dictionaries, each containing at least a "codeCVM" key.
            existing_codes (Optional[Set[str]], optional): Set of CVM codes to skip during processing. Defaults to None.
            save_callback (Optional[Callable[[List[CompanyDataRawDTO]], None]], optional):
                Callback function to save buffered company details periodically.
                Defaults to None.
            threshold (Optional[int], optional): Number of companies to process before triggering the save_callback. If not provided, uses configuration or defaults to 50.
            max_workers (int | None, optional): Reserved for future parallel fetching.
        Returns:
            ExecutionResultDTO[CompanyDataRawDTO]: Fetched company detail DTOs and
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

            company_name = self.datacleaner.clean_text(entry.get("companyName"))
            if company_name in self.existing_codes:
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
            # Buffer each fetched company and flush when threshold is hit
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

    def _fetch_page(self, page_number: int) -> PageResultDTO:
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
        bytes_downloaded = len(body)
        data = json.loads(body.decode("utf-8"))

        results = data.get("results", [])
        total_pages = data.get("page", {}).get("totalPages", 1)

        # self.logger.log("End  Method CompanyDataScraper._fetch_companies_list().processor()_fetch_page()", level="info")

        return PageResultDTO(
            items=results,
            total_pages=total_pages,
            bytes_downloaded=bytes_downloaded,
        )

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""

        return self._metrics_collector
