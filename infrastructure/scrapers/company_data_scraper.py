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

# Generic type variable for list/payload helpers
T = TypeVar("T")


class CompanyDataScraper(CompanyDataScraperPort):
    """Scraper adapter responsible for fetching raw company data.

    In a real implementation, this adapter could orchestrate HTTP calls
    (requests/async clients), HTML parsing (BeautifulSoup), or automation
    (Selenium), depending on the configured port/adapter.

    Attributes:
        config (ConfigPort): Global configuration provider.
        logger (LoggerPort): Logging abstraction for progress/diagnostics.
        data_cleaner (DataCleanerPort): Text normalization and cleaning utilities.
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
    ):
        # Fixed pagination defaults used by the remote API
        self.PAGE_NUMBER = 1
        self.PAGE_SIZE = 120

        # Store core collaborators for use throughout the scraper
        self.config = config
        self.logger = logger
        self.data_cleaner = datacleaner
        self.mapper = mapper
        self.worker_pool_executor = worker_pool
        self._metrics_collector = metrics_collector

        # Shared HTTP client for connection reuse, rate limiting and caching
        self.http_client = http_client

        # Resolve language and endpoints from configuration
        self.language = self.config.exchange.language
        self.endpoint_companies_list = config.exchange.company_data_endpoint["initial"]
        self.endpoint_detail = config.exchange.company_data_endpoint["detail"]
        self.endpoint_financial = config.exchange.company_data_endpoint["financial"]

        # Initialize helper for human-readable byte sizes
        self.byte_formatter = ByteFormatter()

        # Deferred imports to avoid circular dependencies or heavy imports at module load
        from application.mappers.company_data_merger import CompanyDataMerger
        from application.processors.entry_cleaner import EntryCleaner
        from infrastructure.scrapers.company_detail_scraper import DetailFetcher
        # Note: CompanyDataDetailProcessor is referenced below; assumed available in scope
        # via the commented import group or equivalent wiring elsewhere.

        # Compose processors used by the detail pipeline
        self.company_data_merger = CompanyDataMerger(self.mapper, self.logger)
        self.entry_cleaner = EntryCleaner(self.data_cleaner)
        self.detail_fetcher = DetailFetcher(
            http_client=self.http_client,
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
        skip_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[CompanyDataDTO]], None]] = None,
        **kwargs,
    ) -> List[CompanyDataDTO]:
        """Fetch the full set of companies and their details, optionally saving in batches.

        This method first retrieves the paginated company list, then fetches and
        parses details for each company. Optionally, it periodically flushes
        buffered results via ``save_callback`` according to ``threshold``.

        Args:
            threshold (Optional[int]): Number of companies to buffer before flushing.
                Falls back to repository configuration or 50 if not provided.
            skip_codes (Optional[List[str]]): Collection of company identifiers to skip.
            save_callback (Optional[Callable[[List[CompanyDataDTO]], None]]):
                Callback to persist buffered DTOs when the threshold is reached.
            **kwargs: Reserved for future extensions.

        Returns:
            List[CompanyDataDTO]: Fully parsed company detail DTOs.
        """
        # Normalize list of codes to a set for O(1) membership checks
        self.skip_codes = skip_codes or set()

        # Determine persistence threshold (explicit > config > default)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50

        # No-op callback used when only building the initial list
        def noop(_buffer: List[Dict]) -> None:
            return None

        # 1) Fetch the initial list of companies (optionally flushing to storage)
        companies_list = self._fetch_companies_list(save_callback=noop)

        # 2) Fetch and parse detailed data for each company
        companies = self._fetch_companies_details(
            companies_list=companies_list.items,
            save_callback=save_callback,
        )

        # Return the full collection of parsed company details
        return companies

    def _fetch_companies_list(
        self,
        save_callback: Optional[Callable[[List[Dict]], None]] = None,
    ) -> List[CompanyDataDTO]:
        """Fetch the initial set of companies available on the exchange.

        The method handles pagination, incremental buffering (via SaveStrategy),
        metrics reporting, and optional parallel page fetching.

        Args:
            save_callback (Optional[Callable[[List[Dict]], None]]): Optional sink to
                persist items while streaming through pages.

        Returns:
            List[CompanyDataDTO]: Container with items and pagination metadata.
                (Assumes a DTO with ``items`` and ``total_pages`` attributes.)
        """
        # Build a save strategy to flush items while iterating pages
        strategy: SaveStrategy[Dict] = SaveStrategy.from_config(
            save_callback, self.threshold, config=self.config
        )

        # Accumulate all page results for the final merged list
        results = []

        # Start from the first page (API is 1-based)
        page = 1

        # Track network bytes for this page to log incremental download size
        download_bytes_pre = self._metrics_collector.network_bytes

        # Fetch first page to discover total pages and seed results
        fetch = self._fetch_page(page)

        # Compute bytes downloaded during this call
        download_bytes_pos = self._metrics_collector.network_bytes - download_bytes_pre

        # Read total pages from the first response
        total_pages = fetch.total_pages

        # Seed the aggregate results and stream to the strategy
        results = list(fetch.items)
        for item in fetch.items:
            strategy.handle(item)

        # Extra diagnostic info for logging and progress observers
        extra_info = {
            "Download": self.byte_formatter.format_bytes(download_bytes_pos),
            "Total download": self.byte_formatter.format_bytes(
                self.metrics_collector.network_bytes
            ),
        }

        # NOTE: start_time is used here, assumed to be defined by the caller context.
        # If undefined at runtime, this will raise; preserved intentionally (no code changes).
        self.logger.log(
            f"Page {page}/{total_pages}",
            level="info",
            progress={
                "index": 0,
                "size": total_pages,
                "start_time": start_time,  # noqa: F821 (assumed provided in context)
            },
            extra=extra_info,
        )

        # If more pages exist, dispatch them through the worker pool
        if total_pages > 1:
            # Prepare (index, page_number) tasks for pages 2..N
            tasks = list(enumerate(range(2, total_pages + 1)))

            # Worker function that fetches and logs one page
            def processor(task: WorkerTaskDTO) -> PageResultDTO:  # noqa: F821 (assumed DTO)
                # Track network bytes for this page
                download_bytes_pre = self._metrics_collector.network_bytes

                # Fetch the requested page
                fetch = self._fetch_page(task.data)

                # Compute bytes downloaded for this page
                download_bytes_pos = (
                    self._metrics_collector.network_bytes - download_bytes_pre
                )

                # Prepare diagnostics for this worker's page
                extra_info = {
                    "Download": self.byte_formatter.format_bytes(download_bytes_pos),
                    "Total download": self.byte_formatter.format_bytes(
                        self.metrics_collector.network_bytes
                    ),
                }

                # Report progress for this page
                self.logger.log(
                    f"Page {task.data}/{total_pages}",
                    level="info",
                    progress={
                        "index": task.index + 1,
                        "size": total_pages,
                        "start_time": start_time,  # noqa: F821
                    },
                    extra=extra_info,
                    worker_id=task.worker_id,
                )

                # Return the page payload to be merged by the caller
                return fetch

            # Execute worker tasks concurrently
            page_exec = self.worker_pool_executor.run(
                tasks=tasks,
                processor=processor,
                logger=self.logger,
            )

            # Merge items from each fetched page into the result set
            for page_data in page_exec.items:
                results.extend(page_data.items)

        # Finalize the save strategy to flush any remaining buffered items
        strategy.finalize()

        # Return a typed container as declared by the signature (assumed framework-provided)
        return List[CompanyDataDTO]

    def _fetch_companies_details(
        self,
        companies_list: List[Dict],
        save_callback: Optional[Callable[[List[CompanyDataDTO]], None]] = None,
    ) -> List[CompanyDataDTO]:
        """Fetch and parse detailed info for a list of companies.

        Streams companies through a detail processor and buffers parsed results,
        periodically flushing via ``save_callback`` according to the configured
        threshold. Skips entries present in ``self.skip_codes``.

        Args:
            companies_list (List[Dict]): Raw company entries with at least ``codeCVM``.
            save_callback (Optional[Callable[[List[CompanyDataDTO]], None]]):
                Sink to persist buffered detail DTOs.

        Returns:
            List[CompanyDataDTO]: Parsed company detail DTOs.

        Logs:
            Progress for each processed company, including per-item download bytes.

        Notes:
            This method relies on several DTOs (e.g., ExecutionResultDTO,
            CompanyDataRawDTO) assumed to be provided by the surrounding codebase.
            No behavior is changed here; comments clarify intent only.
        """
        # Build a save strategy that buffers detail DTOs and flushes on threshold
        strategy: SaveStrategy[CompanyDataRawDTO] = SaveStrategy(  # noqa: F821 (assumed type)
            save_callback, self.threshold, config=self.config
        )

        # Initialize execution result with baseline metrics
        detail_exec: ExecutionResultDTO[Optional[CompanyDataRawDTO]] = (  # noqa: F821
            ExecutionResultDTO(items=[], metrics=self.metrics_collector.get_metrics(0))  # noqa: F821
        )

        # Pair each entry with its index for progress reporting
        tasks = list(enumerate(companies_list))

        # Mark the start time for progress ETA computations
        start_time = time.perf_counter()

        # Worker that processes a single company entry through the detail pipeline
        def processor(task: WorkerTaskDTO) -> Optional[CompanyDataRawDTO]:  # noqa: F821
            index = task.index
            entry = task.data
            worker_id = task.worker_id

            # Normalize the company name before comparisons/logging
            company_name = self.data_cleaner.clean_text(entry.get("companyName"))

            # Skip if company is already persisted or filtered out
            if company_name in self.skip_codes:
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

            # Track network bytes prior to detail fetch
            download_bytes_pre = self._metrics_collector.network_bytes

            # Process one entry through fetch + clean + merge
            result = self.detail_processor.process_entry(entry)

            # Compute per-item bytes downloaded
            download_bytes_pos = (
                self._metrics_collector.network_bytes - download_bytes_pre
            )

            # Prepare diagnostic metadata for logs
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

            # Return the parsed detail (or None if skipped/failed)
            return result

        # Handler that buffers items and triggers flushes via the strategy
        def handle_batch(item: Optional[CompanyDataRawDTO]) -> None:  # noqa: F821
            # Only buffer non-empty results
            if item is not None:
                strategy.handle([item])

        # Execute detail processing concurrently
        detail_exec = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
        )

        # Ensure any residual buffered items are flushed
        strategy.finalize()

        # Filter out None results from the execution
        results = [item for item in detail_exec.items if item is not None]

        # Return aggregated results and preserve execution metrics
        return ExecutionResultDTO(items=results, metrics=detail_exec.metrics)  # noqa: F821

    def _encode_payload(self, payload: dict) -> str:
        """Encode a JSON-serializable dict into the base64 format expected by the API.

        Args:
            payload (dict): JSON-serializable payload.

        Returns:
            str: Base64-encoded JSON string.
        """
        # Convert payload to base64(JSON(payload))
        return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    def _fetch_page(self, page_number: int) -> list[T]:
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
            body = self.http_client.fetch_with(session, url)

        # Update network metrics with the size of the downloaded payload
        self._metrics_collector.add_network_bytes(len(body))

        # Decode the JSON body to extract results and pagination info
        data = json.loads(body.decode("utf-8"))

        # Read entries for this page
        results = data.get("results", [])

        # Read total pages (some callers expect this for progress)
        total_pages = data.get("page", {}).get("totalPages", 1)

        # Return the raw results list; callers may also access other metadata
        return results

    # @property
    # def metrics_collector(self) -> MetricsCollectorPort:
    #     """Metrics collector used by the scraper."""
    #
    #     return self._metrics_collector
