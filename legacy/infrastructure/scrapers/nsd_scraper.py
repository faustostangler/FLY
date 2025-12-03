"""Scraper for NSD (financial statements) web pages."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from domain.dto import ExecutionResultDTO, NsdDTO, WorkerTaskDTO
from domain.ports import (
    ConfigPort,
    LoggerPort,
    MetricsCollectorPort,
    RepositoryNsdPort,
    ScraperNsdPort,
    WorkerPoolPort,
)
from infrastructure.helpers import ByteFormatter, SaveStrategy
from infrastructure.helpers.datacleaner import DataCleaner
from infrastructure.http.affinity_port import AffinityHttpClient


class NsdScraper(ScraperNsdPort):
    """Scraper adapter responsible for fetching raw NSD documents."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        datacleaner: DataCleaner,
        worker_pool_executor: WorkerPoolPort,
        metrics_collector: MetricsCollectorPort,
        repository: RepositoryNsdPort,
        http_client: AffinityHttpClient,
    ):
        """Set up configuration, logger, and helper utilities for the
        scraper."""
        # Store configuration and logger for use throughout the scraper
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.worker_pool_executor = worker_pool_executor
        self._metrics_collector = metrics_collector
        self.repository = repository

        self.nsd_endpoint = self.config.exchange.nsd_endpoint
        self.http_client = http_client

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[NsdDTO]], None]] = None,
        start: int = 1,
        max_nsd: Optional[int] = None,
        **kwargs,
    ) -> ExecutionResultDTO[NsdDTO]:
        """Fetch and parse NSD pages using a worker queue."""

        # self.logger.log(
        #     "Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()",
        #     level="info",
        # )
        byte_formatter = ByteFormatter()

        self.existing_codes = {int(code) for code in existing_codes} if existing_codes else set()

        start = max(start, max(self.existing_codes, default=0) + 1)

        max_nsd_existing = max_nsd or self._find_last_existing_nsd(start=start) or 50
        max_nsd_probable = max_nsd or self._find_next_probable_nsd(start=start) or 50
        max_nsd = max(start, max_nsd_existing, max_nsd_probable)

        nsd_diff = max_nsd - start

        threshold = threshold or self.config.repository.persistence_threshold or 50

        self.logger.log("Fetch NSD list", level="info")

        if len(self.existing_codes) > nsd_diff:
            codes = list(range(start, max_nsd + 1)) + list(range(1, start - 1))
            codes = [c for c in codes if c not in self.existing_codes]
        else:
            codes = list(range(start, max_nsd + 1))

        tasks = list(enumerate(codes))

        strategy: SaveStrategy[NsdDTO] = SaveStrategy(
            save_callback, threshold, config=self.config
        )

        start_time = time.perf_counter()

        def processor(task: WorkerTaskDTO) -> Optional[NsdDTO]:
            # self.logger.log(
            #     "Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()",
            #     level="info",
            # )
            nsd = task.data

            progress = {
                "index": task.index,
                "size": len(tasks),
                "start_time": start_time,
            }

            if nsd in self.existing_codes:
                self.logger.log(
                    f"{nsd}", level="info", progress=progress, worker_id=worker_id
                )
                return None

            url = self.nsd_endpoint.format(nsd=nsd)

            try:
                with self.http_client.borrow_session() as session:
                    body = self.http_client.fetch_with(session, url, headers=session.headers)
                fetched = self._parse_html(nsd, body.decode("utf-8"))
                # we now persist by company_name, no CVM lookup needed
            # ————————————————————————————————————————————————————————————————

            # self.logger.log(
            #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()._parse_html()",
            #     level="info",
            # )
            except Exception as e:
                self.logger.log(
                    f"Failed to fetch NSD {nsd}: {e}",
                    level="warning",
                    progress=progress,
                    worker_id=worker_id,
                )
                return None

            if fetched:
                download_bytes = len(body)
                extra_info = [
                    fetched["sent_date"].strftime("%Y-%m-%d %H:%M:%S")
                    if fetched.get("sent_date") is not None
                    else "",
                    fetched.get("nsd_type", ""),
                    fetched.get("company_name", ""),
                    fetched["quarter"].strftime("%Y-%m-%d")
                    if fetched.get("quarter") is not None
                    else "",
                    f"{byte_formatter.format_bytes(download_bytes)} {byte_formatter.format_bytes(self.metrics_collector.network_bytes)}",
                ]
            else:
                extra_info = []

            self.logger.log(
                f"{nsd}",
                level="info",
                progress={**progress, "extra_info": extra_info},
                worker_id=worker_id,
            )

            # self.logger.log(
            #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()",
            #     level="info",
            # )

            return NsdDTO.from_dict(fetched)

        def handle_batch(item: Optional[NsdDTO]) -> None:
            if item is not None:
                strategy.handle([item])
            else:
                pass

        # self.logger.log(
        #     "Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().worker_pool_executor.run()",
        #     level="info",
        # )
        exec_result = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
        )
        # self.logger.log(
        #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().worker_pool_executor.run()",
        #     level="info",
        # )

        strategy.finalize()

        # self.logger.log(
        #     f"Downloaded {self.metrics_collector.network_bytes} bytes",
        #     level="info",
        # )

        results = [item for item in exec_result.items if item is not None]

        # self.logger.log(
        #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()",
        #     level="info",
        # )

        return ExecutionResultDTO(items=results, metrics=exec_result.metrics)

    def _parse_html(self, nsd: int, html: str) -> Dict:
        """Parse NSD HTML into a dictionary."""
        soup = BeautifulSoup(html, "html.parser")

        def text_of(selector: str) -> Optional[str]:
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else None

        sent_date = text_of("#lblDataEnvio")
        if not sent_date:
            return {}

        # from DTO
        data: Dict[str, str | int | datetime | None] = {
            "nsd": nsd,
            "company_name": self.datacleaner.clean_text(text_of("#lblNomeCompanhia")),
            # quarter e sent_date serão preenchidos depois
            "quarter": None,
            "version": None,
            "nsd_type": None,
            "dri": None,
            "auditor": None,
            "responsible_auditor": self.datacleaner.clean_text(
                text_of("#lblResponsavelTecnico")
            ),
            "protocol": text_of("#lblProtocolo"),
            "sent_date": None,
            "reason": self.datacleaner.clean_text(
                text_of("#lblMotivoCancelamentoReapresentacao")
            ),
        }

        # Limpeza do padrão FCA
        dri = self.datacleaner.clean_text(text_of("#lblNomeDRI")) or ""
        dri_pattern = r"\s+FCA(?:\s+V\d+)?\b"
        data["dri"] = re.sub(dri_pattern, "", dri)
        data["dri"] = re.sub(r"\s{2,}", " ", data["dri"]).strip()

        auditor = self.datacleaner.clean_text(text_of("#lblAuditor")) or ""
        auditor_pattern = r"\s+FCA\s+\d{4}(?:\s+V\d+)?\b"
        data["auditor"] = re.sub(auditor_pattern, "", auditor)
        data["auditor"] = re.sub(r"\s{2,}", " ", data["auditor"]).strip()

        quarter = text_of("#lblDataDocumento")
        if quarter and quarter.strip().isdigit() and len(quarter.strip()) == 4:
            quarter = f"31/12/{quarter.strip()}"
        data["quarter"] = self.datacleaner.cleandate(quarter) if quarter else None

        nsd_type_version = text_of("#lblDescricaoCategoria")
        if nsd_type_version:
            parts = [p.strip() for p in nsd_type_version.split(" - ")]
            if len(parts) >= 2:
                data["version"] = (
                    self.datacleaner.clean_text(parts[-1]) if parts[-1] else None
                )
                data["nsd_type"] = (
                    self.datacleaner.clean_text(parts[0]) if parts[0] else None
                )

        data["sent_date"] = (
            self.datacleaner.cleandate(sent_date) if sent_date else None
        )

        return data

    def _find_last_existing_nsd(self, start: int = 1, max_limit: int = 10**10) -> int:
        """Return the nsd_highest NSD number that exists.

        The algorithm performs a linear search folnsd_lowed by exponential and
        finally binary search to find the last valid NSD within ``max_limit``.

        Args:
            start: Initial NSD number to try.
            max_limit: Safety upper bound for NSD probing.

        Returns:
            int: The last NSD with valid content.
        """
        nsd = start - 1
        last_valid = None

        max_linear_holes = self.config.scraping.linear_holes or 2000
        hole_count = 0

        # Phase 1: linear search to find the first valid NSD
        while nsd <= max_limit and hole_count < max_linear_holes:
            # Try sequential NSDs until one is valid or the hole limit is reached
            fetched = self._try_nsd(nsd)
            if fetched:
                last_valid = nsd
                break
            nsd += 1
            hole_count += 1

        # Phase 2: exponential search to locate an invalid boundary
        multiplier = 1
        while nsd <= max_limit and hole_count < max_linear_holes:
            fetched = self._try_nsd(nsd)
            if fetched:
                last_valid = nsd
                multiplier += 1
                nsd = nsd * multiplier
            else:
                break

        # If nothing valid was found at all, fall back to ``start``
        if last_valid is None:
            return start

        # Phase 3: binary search between last valid and first invalid
        nsd_low = last_valid or 1
        nsd_high = nsd - 1

        while nsd_low < nsd_high:
            nsd_mid = (
                nsd_low + nsd_high + 1
            ) // 2  # arredonda para cima para evitar loop infinito
            # nsd_diff = nsd_high - nsd_low
            fetched = self._try_nsd(nsd_mid)

            if fetched:
                nsd_low = nsd_mid  # é válido, sobe o piso
            else:
                nsd_high = nsd_mid - 1  # é inválido, desce o teto

        return nsd_low

    def _try_nsd(self, nsd: int) -> Optional[dict]:
        """Attempt to fetch and parse a single NSD page."""
        try:
            # Request the NSD page and parse its HTML
            url = self.nsd_endpoint.format(nsd=nsd)
            body = self.http_client.fetch(url)
            fetched = self._parse_html(nsd, body.decode("utf-8"))

            # Only return results if the page contains a "sent_date" field
            return fetched if fetched.get("sent_date") else None
        except Exception:
            # Ignore any network or parsing errors
            return None

    def _find_next_probable_nsd(
        self,
        start: int = 1,
        safety_factor: float = 1.10,
    ) -> int:
        """Estimate next NSD numbers based on historical submission rate.

        The prediction is calculated from the most recent ``window_days`` worth
        of stored records. It computes the average number of submissions per
        day and multiplies by the number of days since the last known NSD. The
        ``safety_factor`` parameter is applied to avoid underestimation.

        Args:
            repository: Data source providing access to stored NSDs.
            window_days: Number of days used to calculate the average rate.
            safety_factor: Multiplier to account for variations in publishing
                behaviour.

        Returns:
            A list of sequential NSD values likely to have been published
            after the last stored record.
        """
        # Get all nsd with valid sent_date
        if not self.existing_codes:
            return start

        dates = [d for (d,) in self.repository.iter_existing_by_columns("sent_date")]

        first_date = min(dates)
        last_date = max(dates)

        # Days span between dates
        total_span_days = (last_date - first_date).days or 1  # type: ignore[assignment]

        # Daily nsd per day Average
        daily_avg = len(self.existing_codes) / total_span_days

        # days elapsed since last_date
        days_elapsed = max((datetime.now() - last_date).days, 0)  # type: ignore[assignment]

        # Estimated nsd
        last_estimated_nsd = (
            start
            + int(daily_avg * days_elapsed * safety_factor)
            + self.config.scraping.linear_holes
        )

        return last_estimated_nsd
