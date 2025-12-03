from __future__ import annotations

import base64
import json
import time
from typing import Any, Dict, Iterable, List, Optional, TypeVar

from application.mappers.company_data_mapper import CompanyDataMapper
from application.mappers.company_data_merger import CompanyDataMerger
from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.uow_port import Uow, UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.processors.company_detail_processor import CompanyDataDetailProcessor
from application.processors.entry_cleaner import EntryCleaner
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.fetch_results_dto import FetchResultDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.datacleaner_port import DataCleanerPort
from domain.ports.scraper_base_port import ExistingItem, SaveCallback
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from infrastructure.scrapers.scraper_company_detail import DetailFetcher

# <<<<<<< codex/fix-uow-propagation-in-companydatascraper-3sz01n
# =======
# # from domain.ports.scraper_base_port import SaveCallback
# from infrastructure.utils.save_strategy import SaveCallback, SaveStrategy
# >>>>>>> 2025-09-09-Fetch-Adjustments
from infrastructure.utils.byte_formatter import ByteFormatter
from infrastructure.utils.save_strategy import SaveStrategy

# from infrastructure.scrapers.company_data_processors import (
#     CompanyDataDetailProcessor,
#     CompanyDataMerger,
#     DetailFetcher,
#     EntryCleaner,
# )

# Generic type variable for list/payload helpers
T = TypeVar("T")


class CompanyDataScraper(ScraperCompanyDataPort):
    """Scraper adapter responsible for fetching raw company data.

    In a real implementation, this adapter could orchestrate HTTP calls
    (requests/async clients), HTML parsing (BeautifulSoup), or automation
    (Selenium), depending on the configured port/adapter.

    Attributes:
        config (ConfigPort): Global configuration provider.
        logger (LoggerPort): Logging abstraction for progress/diagnostics.
        datacleaner (DataCleanerPort): Text normalization and cleaning utilities.
        mapper (CompanyDataMapper): Maps raw records into domain DTOs.
        worker_pool_executor (WorkerPoolPort): Concurrency execution engine.
        _metrics_collector (MetricsCollectorPort): Network/processing metrics.
        http_client (AffinityHttpClientPort): Shared HTTP client with pooling/limits.
        language (str): Target language for API requests.
        endpoint_companies_list (str): Base URL for initial companies list.
        endpoint_detail (str): Base URL for detailed company endpoint.
        endpoint_financial (str): Base URL for financial endpoint.
        byte_formatter (ByteFormatter): Utility to format byte sizes.
        company_data_merger: Merges detail fragments into a unified record.
        entry_cleaner: Cleans raw entries prior to mapping/merge.
        detail_fetcher: Fetches per-company details from the API.
        detail_processor: Orchestrates fetch + clean + merge for a single entry.
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
        uow_factory: UowFactoryPort,
    ):
        # Fixed pagination defaults used by the remote API
        self.PAGE_NUMBER = 1
        self.PAGE_SIZE = 120

        # Store core collaborators for use throughout the scraper
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.mapper = mapper
        
        self.worker_pool_executor = worker_pool
        self._metrics_collector = metrics_collector
        self.uow_factory = uow_factory

        # Shared HTTP client for connection reuse, rate limiting and caching
        self.http_client = http_client

        # Resolve language and endpoints from configuration
        self.language = self.config.exchange.language
        self.endpoint_companies_list = config.exchange.company_data_endpoint["initial"]
        self.endpoint_detail = config.exchange.company_data_endpoint["detail"]
        self.endpoint_financial = config.exchange.company_data_endpoint["financial"]

        # Initialize helper for human-readable byte sizes
        self.byte_formatter = ByteFormatter()

        # Compose processors used by the detail pipeline
        self.company_data_merger = CompanyDataMerger(self.mapper, self.logger)
        self.entry_cleaner = EntryCleaner(self.datacleaner)
        self.detail_fetcher = DetailFetcher(
            http_client=self.http_client,
            metrics_collector=self._metrics_collector,
            endpoint_detail=self.endpoint_detail,
            language=self.language,
        )
        # Orchestrator that fetches + cleans + merges one company entry
        self.detail_processor = CompanyDataDetailProcessor(  # noqa: F821 (assumed defined in runtime wiring)
            cleaner=self.entry_cleaner,
            fetcher=self.detail_fetcher,
            merger=self.company_data_merger,
        )

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[Iterable[ExistingItem]] = None,
        save_callback: SaveCallback[CompanyDataDTO] | None = None,
        **kwargs,
    ) -> List[CompanyDataDTO]:
        """Fetch the full set of companies and their details, optionally saving in batches.

        This method first retrieves the paginated company list, then fetches and
        parses details for each company. Optionally, it periodically flushes
        buffered results via ``save_callback`` according to ``threshold``.

        Args:
            threshold (Optional[int]): Number of companies to buffer before flushing.
                Falls back to repository configuration or 50 if not provided.
            existing_codes (Optional[Iterable[ExistingItem]]): Collection of company identifiers to skip.
            save_callback (Optional[SaveCallback[CompanyDataDTO]]):
                Callback to persist buffered DTOs when the threshold is reached.
            **kwargs: Reserved for future extensions.

        Returns:
            List[CompanyDataDTO]: Fully fetched company detail DTOs.
        """
        # Normalize list of codes to a set for O(1) membership checks
        self.existing_codes = {
            code for code in (existing_codes or []) if isinstance(code, str)
        }

        # Determine persistence threshold (explicit > config > default)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50

        # No-op callback used when only building the initial list
        def _adapter(items: List[Dict[str, Any]], *, uow: Uow) -> None:
# =======
#         def _adapter(_items: List[Dict[str, Any]], *, uow: Uow) -> None:
# >>>>>>> 2025-09-09-Fetch-Adjustments
            return None

        # 1) Fetch the initial list of companies (optionally flushing to storage)
        companies_entries: List[Dict[str, Any]] = self._fetch_companies_list(
            save_callback=_adapter
        )

        # 2) Fetch and parse detailed data for each company
        companies: List[CompanyDataDTO] = self._fetch_companies_details(
            companies_list=companies_entries,
            save_callback=save_callback,
        )

        # Return the full collection of fetched company details
        return companies

    def _fetch_companies_list(
        self,
        save_callback: SaveCallback[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """Fetch the initial set of companies available on the exchange.

        The method handles pagination, incremental buffering (via SaveStrategy),
        metrics reporting, and optional parallel page fetching.

        Args:
            save_callback (Optional[SaveCallback[Dict[str, Any]]]): Optional sink to
                persist items while streaming through pages.

        Returns:
            List[CompanyDataDTO]: Container with items and pagination metadata.
                (Assumes a DTO with ``items`` and ``total_pages`` attributes.)
        """
        # time counter
        start_time = time.perf_counter()

        # adapta callback do porto (items) para a estratégia (items, *, uow)
        def _adapter(items: List[Dict[str, Any]], *, uow: Uow) -> None:
            if save_callback is not None:
                save_callback(items, uow=uow)


        # Build a save strategy to flush items while iterating pages
        strategy: SaveStrategy[Dict[str, Any]] = SaveStrategy.from_config(
            _adapter if save_callback else None,
            self.threshold,
            config=self.config,
            uow_factory=self.uow_factory,
        )

        # Accumulate all page results for the final merged list
        companies_list: List[Dict[str, Any]] = []

        # Start from the first page (API is 1-based)
        page = 1

        # Fetch first page to discover total pages and seed results
        fetch_first = self._fetch_page(page)

        # Include FetchResultDTO items in items list
        companies_list.extend(fetch_first.items)

        # Seed the aggregate results and stream to the strategy
        for item in fetch_first.items:
            strategy.handle(item)

        # Extra diagnostic info for logging and progress observers
        extra_info = {
            "Download": self.byte_formatter.format_bytes(
                self._metrics_collector.download_bytes
            ),
            "Total download": self.byte_formatter.format_bytes(
                self._metrics_collector.network_bytes
            ),
        }

        # Log Progress
        self.logger.log(
            f"Page {page}/{fetch_first.total_pages}",
            level="info",
            progress={
                "index": 0,
                "size": fetch_first.total_pages,
                "start_time": start_time,  # noqa: F821 (assumed provided in context)
            },
            extra=extra_info,
        )

        # If more pages exist, dispatch them through the worker pool
        if fetch_first.total_pages > 1:
            # Prepare (index, page_number) tasks for pages 2..N
            tasks = list(enumerate(range(2, fetch_first.total_pages + 1)))

            # Worker function that fetches and logs one page
            def processor(task: WorkerTaskDTO) -> FetchResultDTO:
                # Fetch the requested page
                fetch_next = self._fetch_page(task.data)

                # Prepare diagnostics for this worker's page
                extra_info = {
                    "Download": self.byte_formatter.format_bytes(
                        self._metrics_collector.download_bytes
                    ),
                    "Total download": self.byte_formatter.format_bytes(
                        self._metrics_collector.network_bytes
                    ),
                }

                # Report progress for this page
                self.logger.log(
                    f"Page {task.data}/{fetch_next.total_pages}",
                    level="info",
                    progress={
                        "index": task.index + 1,
                        "size": fetch_next.total_pages,
                        "start_time": start_time,  # noqa: F821
                    },
                    extra=extra_info,
                    worker_id=task.worker_id,
                )

                # Return the page payload to be merged by the caller
                return fetch_next

            # Execute worker tasks concurrently
            results: List[FetchResultDTO] = self.worker_pool_executor.run(
                tasks=tasks,
                processor=processor,
                logger=self.logger,
                max_workers=1,
            )

            # Merge items from each fetched page into the result set
            for fetch_results_dto in results:
                companies_list.extend(fetch_results_dto.items)

        # Finalize the save strategy to flush any remaining buffered items
        strategy.finalize()

        # Return a typed container as declared by the signature (assumed framework-provided)
        return companies_list

    def _fetch_companies_details(
        self,
        companies_list: List[Dict],
        save_callback: SaveCallback[CompanyDataDTO] | None = None,
    ) -> List[CompanyDataDTO]:
        """Fetch and parse detailed info for a list of companies.

        Streams companies through a detail processor and buffers fetched results,
        periodically flushing via ``save_callback`` according to the configured
        threshold. Skips entries present in ``self.existing_codes``.

        Args:
            companies_list (List[Dict]): Raw company entries with at least ``codeCVM``.
            save_callback (Optional[SaveCallback[CompanyDataDTO]]):
                Sink to persist buffered detail DTOs.

        Returns:
            List[CompanyDataDTO]: Fetched company detail DTOs.

        Logs:
            Progress for each processed company, including per-item download bytes.

        Notes:
            This method relies on several DTOs (e.g., ExecutionResultDTO,
            CompanyDataRawDTO) assumed to be provided by the surrounding codebase.
            No behavior is changed here; comments clarify intent only.
        """

        # adapter para a estratégia
        def _adapter(items: List[CompanyDataDTO], *, uow: Uow) -> None:
            if save_callback is not None:
                save_callback(items, uow=uow)

        # Build a save strategy that buffers detail DTOs and flushes on threshold
        strategy: SaveStrategy[CompanyDataDTO] = SaveStrategy.from_config(
            _adapter if save_callback else None,
            self.threshold,
            config=self.config,
            uow_factory=self.uow_factory,
        )

        # Pair each entry with its index for progress reporting
        tasks = list(enumerate(companies_list))

        # Mark the start time for progress ETA computations
        start_time = time.perf_counter()

        # Worker that processes a single company entry through the detail pipeline
        def processor(task: WorkerTaskDTO) -> Optional[CompanyDataDTO]:  # noqa: F821
            index = task.index
            entry = task.data
            worker_id = task.worker_id

            # Normalize the company name before comparisons/logging
            company_name = self.datacleaner.clean_text(entry.get("companyName"))

            # Skip if company is already persisted or filtered out
            if company_name in self.existing_codes:
                # Log a concise progress update for the skipped record
                extra_info = {
                    "issuingCompany": entry["issuingCompany"],
                    "trading_name": entry["tradingName"],
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

            # Process one entry through fetch + clean + merge
            result = self.detail_processor.process_entry(entry)

            # Prepare diagnostic metadata for logs
            issuingCompany = (
                result.issuing_company if result else entry.get("issuingCompany")
            )
            tradingName = result.trading_name if result else entry.get("tradingName")
            extra_info = {
                "issuingCompany": issuingCompany,
                "trading_name": tradingName,
                "Download": self.byte_formatter.format_bytes(
                    self._metrics_collector.download_bytes
                ),
                "Total download": self.byte_formatter.format_bytes(
                    self._metrics_collector.network_bytes
                ),
            }

            # Emit structured progress log for this item
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

            # Return the fetched detail (or None if skipped/failed)
            return result

        # Handler that buffers items and triggers flushes via the strategy
        def handle_batch(item: Optional[CompanyDataDTO]) -> None:  # noqa: F821
            # Only buffer non-empty results
            if item is not None:
                strategy.handle(item)

        # Execute detail processing concurrently
        companies = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
            max_workers=self.config.worker_pool.max_workers or 1,
        )

        # Ensure any residual buffered items are flushed
        strategy.finalize()

        # Filter out None results from the execution
        results = [item for item in companies if item is not None]

        # Return aggregated results and preserve execution metrics
        return results

    def _encode_payload(self, payload: dict) -> str:
        """Encode a JSON-serializable dict into the base64 format expected by the API.

        Args:
            payload (dict): JSON-serializable payload.

        Returns:
            str: Base64-encoded JSON string.
        """
        # Convert payload to base64(JSON(payload))
        return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    def _fetch_page(self, page_number: int) -> FetchResultDTO:
        """Fetch one page from the companies list endpoint.

        Builds the required base64 token, performs the HTTP request using the
        shared client, updates network metrics, and returns the raw page results.

        Args:
            page_number (int): 1-based page number.

        Returns:
            list[T]: Raw result entries for the requested page.

        Notes:
            The concrete shape of T is determined by the upstream API and
            mappers; this method deliberately returns the raw items.
        """
        # Build request payload for the target page
        payload = {
            "language": self.language,
            "pageNumber": page_number,
            "pageSize": self.PAGE_SIZE,
        }

        # Encode payload into the API's expected token format
        token = self._encode_payload(payload)

        # Construct the request URL using the encoded token
        url = self.endpoint_companies_list + token

        # Borrow a pooled session to issue the request
        with self.http_client.borrow_session() as session:
            body = self.http_client.fetch_with(session, url, headers=session.headers)

        # Decode the JSON body to extract results and pagination info
        data = json.loads(body.decode("utf-8"))

        # Read entries for this page
        items = data.get("results", [])

        # Read total pages (some callers expect this for progress)
        total_pages = data.get("page", {}).get("totalPages", 1)

        # Return the raw results list; callers may also access other metadata
        return FetchResultDTO(items=items, total_pages=total_pages)

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes
