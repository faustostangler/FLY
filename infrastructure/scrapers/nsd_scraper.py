"""Scraper for NSD (financial statements) web pages."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from domain.dto import ExecutionResultDTO, NsdDTO, WorkerTaskDTO
from domain.ports import (
    LoggerPort,
    MetricsCollectorPort,
    NSDRepositoryPort,
    NSDSourcePort,
    SqlAlchemyCompanyDataRepositoryPort,
    WorkerPoolPort,
)
from infrastructure.config import Config
from infrastructure.helpers import FetchUtils, SaveStrategy
from infrastructure.helpers.data_cleaner import DataCleaner


class NsdScraper(NSDSourcePort):
    """Scraper adapter responsible for fetching raw NSD documents."""

    def __init__(
        self,
        config: Config,
        logger: LoggerPort,
        data_cleaner: DataCleaner,
        worker_pool_executor: WorkerPoolPort,
        metrics_collector: MetricsCollectorPort,
        repository: NSDRepositoryPort,
        company_repository: SqlAlchemyCompanyDataRepositoryPort,  # << novo
    ):
        """Set up configuration, logger, and helper utilities for the
        scraper."""
        # Store configuration and logger for use throughout the scraper
        self.config = config
        self.logger = logger
        self.data_cleaner = data_cleaner
        self.worker_pool_executor = worker_pool_executor
        self._metrics_collector = metrics_collector
        self.repository = repository
        self.company_repo = company_repository

        self.fetch_utils = FetchUtils(config, logger)
        self.session = self.fetch_utils.create_scraper()

        self.nsd_endpoint = self.config.exchange.nsd_endpoint

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        skip_codes: Optional[List[str]] = None,
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

        self.skip_codes = {int(code) for code in skip_codes} if skip_codes else set()

        # start = max(start, max(self.skip_codes, default=0) + 1)

        # max_nsd_existing = max_nsd or self._find_last_existing_nsd(start=start) or 50
        # max_nsd_probable = max_nsd or self._find_next_probable_nsd(start=start) or 50
        # max_nsd = max(max_nsd_existing, max_nsd_probable)

        # threshold = threshold or self.config.global_settings.threshold or 50

        # self.logger.log("Fetch NSD list", level="info")

        # tasks = list(enumerate(range(start, max_nsd + 1)))
        tasks = list(enumerate(range(34, 45)))

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

            if nsd in self.skip_codes:
                self.logger.log(
                    f"{nsd}", level="info", progress=progress, worker_id=task.worker_id
                )
                return None

            url = self.nsd_endpoint.format(nsd=nsd)

            try:
                response, self.session = self.fetch_utils.fetch_with_retry(
                    self.session, url
                )
                self.metrics_collector.record_network_bytes(len(response.content))

                # self.logger.log(
                #     "Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()_parse_html()",
                #     level="info",
                # )
                parsed = self._parse_html(nsd, response.text)
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
                    worker_id=task.worker_id,
                )
                return None

            if parsed:
                extra_info = [
                    f"{parsed.get('nsd', nsd)}",
                    parsed["quarter"].strftime("%Y-%m-%d")
                    if parsed.get("quarter") is not None
                    else "",
                    parsed.get("company_name", ""),
                    parsed.get("nsd_type", ""),
                    parsed["sent_date"].strftime("%Y-%m-%d %H:%M:%S")
                    if parsed.get("sent_date") is not None
                    else "",
                    str(len(response.content)),
                ]
            else:
                extra_info = []

            self.logger.log(
                f"{nsd}",
                level="info",
                progress={**progress, "extra_info": extra_info},
                worker_id=task.worker_id,
            )

            # self.logger.log(
            #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()",
            #     level="info",
            # )

            return NsdDTO.from_dict(parsed)

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
            "company_name": self.data_cleaner.clean_text(text_of("#lblNomeCompanhia")),
            # quarter e sent_date serão preenchidos depois
            "quarter": None,
            "version": None,
            "nsd_type": None,
            "dri": None,
            "auditor": None,
            "responsible_auditor": self.data_cleaner.clean_text(
                text_of("#lblResponsavelTecnico")
            ),
            "protocol": text_of("#lblProtocolo"),
            "sent_date": None,
            "reason": self.data_cleaner.clean_text(
                text_of("#lblMotivoCancelamentoReapresentacao")
            ),
        }

        # Limpeza do padrão FCA
        dri = self.data_cleaner.clean_text(text_of("#lblNomeDRI")) or ""
        dri_pattern = r"\s+FCA(?:\s+V\d+)?\b"
        data["dri"] = re.sub(dri_pattern, "", dri)
        data["dri"] = re.sub(r"\s{2,}", " ", data["dri"]).strip()

        auditor = self.data_cleaner.clean_text(text_of("#lblAuditor")) or ""
        auditor_pattern = r"\s+FCA\s+\d{4}(?:\s+V\d+)?\b"
        data["auditor"] = re.sub(auditor_pattern, "", auditor)
        data["auditor"] = re.sub(r"\s{2,}", " ", data["auditor"]).strip()

        quarter = text_of("#lblDataDocumento")
        if quarter and quarter.strip().isdigit() and len(quarter.strip()) == 4:
            quarter = f"31/12/{quarter.strip()}"
        data["quarter"] = self.data_cleaner.clean_date(quarter) if quarter else None

        nsd_type_version = text_of("#lblDescricaoCategoria")
        if nsd_type_version:
            parts = [p.strip() for p in nsd_type_version.split(" - ")]
            if len(parts) >= 2:
                data["version"] = (
                    self.data_cleaner.clean_text(parts[-1]) if parts[-1] else None
                )
                data["nsd_type"] = (
                    self.data_cleaner.clean_text(parts[0]) if parts[0] else None
                )

        data["sent_date"] = (
            self.data_cleaner.clean_date(sent_date) if sent_date else None
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
        nsd = 34 - 1
        last_valid = None

        max_linear_holes = self.config.global_settings.max_linear_holes or 2000
        hole_count = 0

        # Phase 1: linear search to find the first valid NSD
        while nsd <= max_limit and hole_count < max_linear_holes:
            # Try sequential NSDs until one is valid or the hole limit is reached
            parsed = self._try_nsd(nsd)
            if parsed:
                last_valid = nsd
                break
            nsd += 1
            hole_count += 1

        # Phase 2: exponential search to locate an invalid boundary
        nsd = nsd + 1  # move forward
        multiplier = 0
        while nsd <= max_limit and hole_count < max_linear_holes:
            parsed = self._try_nsd(nsd)
            if parsed:
                last_valid = nsd
                multiplier += 1
                nsd += 2 ** int(multiplier)
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
            parsed = self._try_nsd(nsd_mid)

            if parsed:
                nsd_low = nsd_mid  # é válido, sobe o piso
            else:
                nsd_high = nsd_mid - 1  # é inválido, desce o teto

        return nsd_low

    def _try_nsd(self, nsd: int) -> Optional[dict]:
        """Attempt to fetch and parse a single NSD page."""
        try:
            # Request the NSD page and parse its HTML
            url = self.nsd_endpoint.format(nsd=nsd)
            response, self.session = self.fetch_utils.fetch_with_retry(
                self.session, url
            )
            parsed = self._parse_html(nsd, response.text)

            # Only return results if the page contains a "sent_date" field
            return parsed if parsed.get("sent_date") else None
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
        if not self.skip_codes:
            return start

        first_pk = min(self.skip_codes, key=lambda n: int(n))
        last_pk = max(self.skip_codes, key=lambda n: int(n))
        first_date = self.repository.get_by_id(str(first_pk)).sent_date
        last_date = self.repository.get_by_id(str(last_pk)).sent_date

        # Days span between dates
        total_span_days = (last_date - first_date).days or 1  # type: ignore[assignment]

        # Daily nsd per day Average
        daily_avg = len(self.skip_codes) / total_span_days

        # days elapsed since last_date
        days_elapsed = max((datetime.now() - last_date).days, 0)  # type: ignore[assignment]

        # Estimated nsd
        last_estimated_nsd = (
            start
            + int(daily_avg * days_elapsed * safety_factor)
            + self.config.global_settings.max_linear_holes
        )

        return last_estimated_nsd
