"""Scraper for NSD (financial statements) web pages."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from bs4 import BeautifulSoup

from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.uow_port import Uow
from application.ports.worker_pool_port import WorkerPoolPort
from domain.dtos.nsd_dto import NsdDTO
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_base_port import ExistingItem, SaveCallback
from domain.ports.scraper_nsd_port import ScraperNsdPort
from infrastructure.adapters.datacleaner_adapter import DataCleaner


def _to_int_code(x: Any) -> Optional[int]:
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        m = re.search(r"\d+", x)
        return int(m.group()) if m else None
    if isinstance(x, tuple):
        for part in x:
            v = _to_int_code(part)
            if v is not None:
                return v
        return None
    if isinstance(x, dict):
        for key in ("nsd", "code", "id"):
            if key in x:
                v = _to_int_code(x[key])
                if v is not None:
                    return v
        return None
    return None

class NsdScraper(ScraperNsdPort):
    """Scraper adapter responsible for fetching raw NSD documents."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository_nsd: RepositoryNsdPort,
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

        self.repository_nsd = repository_nsd

        self.datacleaner = datacleaner
        self.worker_pool = worker_pool
        self._metrics_collector = metrics_collector

        self.nsd_endpoint = self.config.exchange.nsd_endpoint
        self.http_client = http_client

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    # Adapter: cumpre (object) -> datetime exigido por NsdDTO.from_dict,
    # reutilizando o DataCleaner.cleandate (str|None) -> datetime|None.
    def _cleandate_required(self, obj: object) -> datetime:
        s: Optional[str] = str(obj) if obj is not None else None
        dt = self.datacleaner.cleandate(s)
        if dt is None:
            raise ValueError(f"Data inválida: {obj}")
        return dt

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[Iterable[ExistingItem]] = None,
        save_callback: Optional[SaveCallback[NsdDTO]] = None,
        **kwargs: Any,
    ) -> List[NsdDTO]:
        # lê parâmetros extras sem quebrar a assinatura da porta
        start = int(kwargs.get("start", 1))
        max_nsd = int(kwargs.get("max_nsd", 1))
        
        codes: List[int] = []
        for c in existing_codes or []:
            v = _to_int_code(c)
            if v is not None:
                codes.append(v)

        items = list(
            self.iter_nsd(
                start=start,
                threshold=threshold,
                existing_codes=codes or None,
                max_nsd=max_nsd,
            )
        )
        return items

    def fetch_one(self, nsd: int) -> NsdDTO | None:
        try:
            url = self.nsd_endpoint.format(nsd=nsd)
            with self.http_client.borrow_session() as session:
                body = self.http_client.fetch_with(session, url, headers=session.headers)
            parsed = self._parse_html(nsd, body.decode("utf-8"))
            return (
                NsdDTO.from_dict(parsed, cleandate=self._cleandate_required)
                if parsed and parsed.get("sent_date")
                else None
            )
        except Exception:
            return None

    def iter_nsd(
        self,
        *,
        start: int = 1,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[int]] = [],  # mantém compatibilidade
        max_nsd: int = 1,
        **kwargs,
    ) -> Iterable[NsdDTO]:

        self.existing_codes = [int(code) for code in existing_codes] if existing_codes else []
        start = max(start, max(self.existing_codes, default=0) + 1)

        top_limit = max(max_nsd, self._find_last_existing_nsd(start=start), 50)

        self.logger.log(f"Using top limit: {top_limit}", level="info")

        self.logger.log(
            f"Streaming NSD from {start} to {top_limit or 'infinity'}, skipping {len(self.existing_codes)} existing",
            level="info",
        )
        for code in range(start, top_limit + 1):
            if code in self.existing_codes:
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

                dto = NsdDTO.from_dict(parsed, cleandate=self._cleandate_required)
                if dto is None:
                    continue  # evita yield de None, satisfaz o type checker
                yield dto

                # aqui não há persistência nem batch; é só streaming
            except Exception as e:
                self.logger.log(f"Failed to fetch NSD: {code} {e}", level="warning")
                continue

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
        q = self.datacleaner.cleandate(quarter) if quarter else None
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
        nsd = start if start == 1 else start + 1
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
        multiplier = 10
        count = 0
        nsd += 1
        while nsd <= max_limit and hole_count < max_linear_holes:
            fetched = self._try_nsd(nsd)
            if fetched:
                last_valid = nsd
                # multiplier += 1
                count += 1
                increment = int(multiplier ** count)
                nsd = last_valid + increment
            else:
                break

        # If nothing valid was found at all, fall back to ``start``
        if last_valid is None:
            return start

        # Phase 3: binary search between last valid and first invalid
        nsd_low = last_valid or 1
        nsd_high = nsd - 1

        while nsd_low < nsd_high:
            count += 1
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

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes
