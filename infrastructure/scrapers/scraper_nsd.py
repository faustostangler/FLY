"""Scraper for NSD (financial statements) web pages."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import  Callable, Dict, List, Iterable, Optional

from bs4 import BeautifulSoup

from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from infrastructure.utils.byte_formatter import ByteFormatter
from infrastructure.utils.save_strategy import SaveStrategy
from infrastructure.adapters.datacleaner_adapter import DataCleaner
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.worker_pool_port import WorkerPoolPort


class NsdScraper(ScraperNsdPort):
    """Scraper adapter responsible for fetching raw NSD documents."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        
        nsd_repository: RepositoryNsdPort,

        datacleaner: DataCleaner,
        metrics_collector: MetricsCollectorPort,
        worker_pool: WorkerPoolPort,
        http_client: AffinityHttpClientPort,
    ):
        """Set up configuration, logger, and helper utilities for the
        scraper."""
        # Store configuration and logger for use throughout the scraper
        self.config = config
        self.logger = logger

        self.nsd_repository = nsd_repository

        self.datacleaner = datacleaner
        self.worker_pool = worker_pool
        self._metrics_collector = metrics_collector

        self.nsd_endpoint = self.config.exchange.nsd_endpoint
        self.http_client = http_client

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def fetch_all(self, threshold: int | None = None, skip_codes: List[str] | None = None, save_callback: Callable[[List[NsdDTO]], None] | None = None, **kwargs) -> List[NsdDTO]:
        return None
    
    def fetch_one(self, nsd: int) -> NsdDTO | None:
        try:
            url = self.nsd_endpoint.format(nsd=nsd)
            with self.http_client.borrow_session() as session:
                body = self.http_client.fetch_with(session, url, headers=session.headers)
            parsed = self._parse_html(nsd, body.decode("utf-8"))
            return NsdDTO.from_dict(parsed) if parsed and parsed.get("sent_date") else None
        except Exception:
            return None

    def iter_nsd(
        self,
        *,
        start: int = 1,
        threshold: Optional[int] = None,  # mantido por compatibilidade, não usado aqui
        skip_codes: Optional[List[int]] = [],  # mantido por compatibilidade, não usado aqui
        max_nsd: int = 1,
        **kwargs,
    ) -> Iterable[NsdDTO]:

        self.skip_codes = [int(code) for code in skip_codes] if skip_codes else []
        start = max(start, max(self.skip_codes, default=0) + 1)
        # top_limit = max(max_nsd, self._find_last_existing_nsd(start=start), 50)

        start = 10008
        top_limit = max_nsd
        self.logger.log(f"Using top limit: {top_limit}", level="info")

        self.logger.log(f"Streaming NSD from {start} to {top_limit or 'infinity'}, skipping {len(self.skip_codes)} existing", level="info")
        for code in range(start, top_limit + 1):
            if code in self.skip_codes:
                self.logger.log(f"Processed NSD: {code} Done", level="info")
                continue
            url = self.nsd_endpoint.format(nsd=code)
            try:
                with self.http_client.borrow_session() as session:
                    body = self.http_client.fetch_with(session, url, headers=session.headers)
                parsed = self._parse_html(code, body.decode("utf-8"))
                if not parsed:
                    self.logger.log(f"Processed NSD: {code} Empty", level="info")
                    continue

                dto = NsdDTO.from_dict(parsed)
                if dto is None:
                    continue  # evita yield de None, satisfaz o type checker
                yield dto

                # aqui não há persistência nem batch; é só streaming
            except Exception as e:
                self.logger.log(f"Failed to fetch NSD: {code} {e}", level="warning")
                continue

    # def fetch_all(
    #     self,
    #     threshold: Optional[int] = None,
    #     skip_codes: Optional[List[str]] = None,
    #     save_callback=None,
    #     start: int = 1,
    #     max_nsd: Optional[int] = None,
    #     **kwargs,
    # ) -> List[NsdDTO]:
    #     return list(self.iter_nsd(
    #         start=start,
    #         threshold=threshold,
    #         skip_codes=skip_codes,
    #         max_nsd=max_nsd,
    #         **kwargs,
    #     ))

    # def fetch_all(
    #     self,
    #     threshold: Optional[int] = None,
    #     skip_codes: Optional[List[str]] = None,
    #     save_callback: Optional[Callable[[List[NsdDTO]], None]] = None,
    #     start: int = 1,
    #     max_nsd: Optional[int] = None,
    #     **kwargs,
    # ) -> List[NsdDTO]:
    #     """Fetch and parse NSD pages using a worker queue."""

    #     # self.logger.log(
    #     #     "Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()",
    #     #     level="info",
    #     # )
    #     byte_formatter = ByteFormatter()

    #     self.skip_codes = {int(code) for code in skip_codes} if skip_codes else set()

    #     start = max(start, max(self.skip_codes, default=0) + 1)

    #     max_nsd_existing = max_nsd or self._find_last_existing_nsd(start=start) or 50
    #     max_nsd_probable = max_nsd or self._find_next_probable_nsd(start=start) or 50
    #     max_nsd = max(start, max_nsd_existing, max_nsd_probable)

    #     nsd_diff = max_nsd - start

    #     threshold = threshold or self.config.repository.persistence_threshold

    #     self.logger.log("Fetch NSD list", level="info")

    #     if len(self.skip_codes) > nsd_diff:
    #         codes = list(range(start, max_nsd + 1)) + list(range(1, start - 1))
    #         codes = [c for c in codes if c not in self.skip_codes]
    #     else:
    #         codes = list(range(start, max_nsd + 1))

    #     tasks = list(enumerate(codes))

    #     strategy: SaveStrategy[NsdDTO] = SaveStrategy.from_config(
    #         save_callback, threshold, config=self.config
    #     )

    #     start_time = time.perf_counter()

    #     def processor(task: WorkerTaskDTO) -> Optional[NsdDTO]:
    #         # self.logger.log(
    #         #     "Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()",
    #         #     level="info",
    #         # )
    #         nsd = task.data

    #         progress = {
    #             "index": task.index,
    #             "size": len(tasks),
    #             "start_time": start_time,
    #         }

    #         if nsd in self.skip_codes:
    #             self.logger.log(
    #                 f"{nsd}", level="info", progress=progress, worker_id=task.worker_id
    #             )
    #             return None

    #         url = self.nsd_endpoint.format(nsd=nsd)

    #         try:
    #             with self.http_client.borrow_session() as session:
    #                 body = self.http_client.fetch_with(session, url, headers=session.headers)
    #             fetched = self._parse_html(nsd, body.decode("utf-8"))
    #             # we now persist by company_name, no CVM lookup needed
    #         # ————————————————————————————————————————————————————————————————

    #         # self.logger.log(
    #         #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()._parse_html()",
    #         #     level="info",
    #         # )
    #         except Exception as e:
    #             self.logger.log(
    #                 f"Failed to fetch NSD {nsd}: {e}",
    #                 level="warning",
    #                 progress=progress,
    #                 worker_id=task.worker_id,
    #             )
    #             return None

    #         if fetched:
    #             download_bytes = len(body)
    #             extra_info = [
    #                 fetched["sent_date"].strftime("%Y-%m-%d %H:%M:%S")
    #                 if fetched.get("sent_date") is not None
    #                 else "",
    #                 fetched.get("nsd_type", ""),
    #                 fetched.get("company_name", ""),
    #                 fetched["quarter"].strftime("%Y-%m-%d")
    #                 if fetched.get("quarter") is not None
    #                 else "",
    #                 f"{byte_formatter.format_bytes(download_bytes)} {byte_formatter.format_bytes(self.metrics_collector.network_bytes)}",
    #             ]
    #         else:
    #             extra_info = []

    #         self.logger.log(
    #             f"{nsd}",
    #             level="info",
    #             progress={**progress, "extra_info": extra_info},
    #             worker_id=task.worker_id,
    #         )

    #         # self.logger.log(
    #         #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().processor()",
    #         #     level="info",
    #         # )

    #         return NsdDTO.from_dict(fetched)

    #     def handle_batch(item: Optional[NsdDTO]) -> None:
    #         if item is not None:
    #             strategy.handle(item)
    #         else:
    #             pass

    #     # self.logger.log(
    #     #     "Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().worker_pool_executor.run()",
    #     #     level="info",
    #     # )
    #     nsds = self.worker_pool.run(
    #         tasks=tasks,
    #         processor=processor,
    #         logger=self.logger,
    #         on_result=handle_batch,
    #         max_workers=self.config.worker_pool.max_workers or 1,
    #     )
    #     # self.logger.log(
    #     #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().worker_pool_executor.run()",
    #     #     level="info",
    #     # )

    #     strategy.finalize()

    #     # self.logger.log(
    #     #     f"Downloaded {self.metrics_collector.network_bytes} bytes",
    #     #     level="info",
    #     # )

    #     results = [item for item in nsds if item is not None]

    #     # self.logger.log(
    #     #     "End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()",
    #     #     level="info",
    #     # )

    #     return results

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
            "sent_date": sent_date,
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
        q = self.datacleaner.clean_date(quarter) if quarter else None
        y = datetime.today().year
        m = datetime.today().month
        if isinstance(q, datetime):
            y, m = q.year, q.month
        # mapeia para o mês de fechamento do trimestre
        mm = 3 if m <= 3 else 6 if m <= 6 else 9 if m <= 9 else 12
        dd = 31 if mm in (3, 12) else 30
        data['quarter'] = datetime(int(y), mm, dd)

        nsd_type_version = text_of("#lblDescricaoCategoria")
        if nsd_type_version:
            parts = [p.strip() for p in nsd_type_version.split(" - ")]
            if len(parts) >= 2:
                version = self.datacleaner.clean_text(parts[-1]) if parts[-1] else "1"
                data["version"] = int(''.join(c for c in str(version or 1) if c.isdigit()))
                data["nsd_type"] = (
                    self.datacleaner.clean_text(parts[0]) if parts[0] else None
                )

        data["sent_date"] = (
            self.datacleaner.clean_date(sent_date) if sent_date else None
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

    # def _find_next_probable_nsd(
    #     self,
    #     start: int = 1,
    #     safety_factor: float = 1.10,
    # ) -> int:
    #     """Estimate next NSD numbers based on historical submission rate.

    #     The prediction is calculated from the most recent ``window_days`` worth
    #     of stored records. It computes the average number of submissions per
    #     day and multiplies by the number of days since the last known NSD. The
    #     ``safety_factor`` parameter is applied to avoid underestimation.

    #     Args:
    #         repository: Data source providing access to stored NSDs.
    #         window_days: Number of days used to calculate the average rate.
    #         safety_factor: Multiplier to account for variations in publishing
    #             behaviour.

    #     Returns:
    #         A list of sequential NSD values likely to have been published
    #         after the last stored record.
    #     """
    #     # Get all nsd with valid sent_date
    #     if not self.skip_codes:
    #         return start

    #     dates = [d for (d,) in self.nsd_repository.iter_existing_by_columns("sent_date")]

    #     first_date = min(dates)
    #     last_date = max(dates)

    #     # Days span between dates
    #     total_span_days = (last_date - first_date).days or 1  # type: ignore[assignment]

    #     # Daily nsd per day Average
    #     daily_avg = len(self.skip_codes) / total_span_days

    #     # days elapsed since last_date
    #     days_elapsed = max((datetime.now() - last_date).days, 0)  # type: ignore[assignment]

    #     # Estimated nsd
    #     last_estimated_nsd = (
    #         start
    #         + int(daily_avg * days_elapsed * safety_factor)
    #         + self.config.scraping.linear_holes
    #     )

    #     return last_estimated_nsd

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

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes
