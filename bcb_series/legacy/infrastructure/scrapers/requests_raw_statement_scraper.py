"""Scrapers: low-level HTTP fetcher and domain-level statements scraper.
This file keeps hexagonal boundaries intact: the domain scraper depends only on the
public HTTP client API (AffinityHttpClient), never on private attributes.
"""

from __future__ import annotations

import contextlib
import re
import time
from typing import Any, Dict, List, Mapping, Sequence
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response

# Domain deps
from domain.dto import WorkerTaskDTO
from domain.dto.nsd_dto import NsdDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.ports import ConfigPort, LoggerPort, MetricsCollectorPort
from domain.ports.scraper_ports import StatementsRawcraperPort

# Infra helpers
from infrastructure.helpers.datacleaner import DataCleaner
from infrastructure.helpers.fetch_utils import FetchUtils
from infrastructure.helpers.time_utils import TimeUtils
from infrastructure.helpers.worker_pool import WorkerPool
from infrastructure.http.affinity_port import AffinityHttpClient
from infrastructure.http.session_pool import SessionPool
from infrastructure.utils.id_generator import IdGenerator


class RequestsStatementsRawcraper:
    """Infra HTTP client with connection reuse.
    Exposes a public API that supports session affinity for a batch of fetches.
    """

    def __init__(
        self,
        pool: SessionPool,
        config: ConfigPort | None = None,
        logger: LoggerPort | None = None,
        metrics: MetricsCollectorPort | None = None,
        timeout: tuple[float, float] = (5.0, 20.0),
    ) -> None:
        self._pool = pool
        self._timeout = timeout
        self._logger = logger
        self._config = config
        self._metrics = metrics

    # ---------- Public API ----------

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Simple GET using pooled sessions."""
        hdrs = dict(headers or {})

        s = self._pool.acquire()
        try:
            r: Response = s.get(url, headers=hdrs, timeout=self._timeout, allow_redirects=True)
        finally:
            self._pool.release(s)

        if r.status_code in (429, 403):
            ex = Exception("rate limited")
            setattr(ex, "status_code", r.status_code)
            raise ex

        r.raise_for_status()

        body = r.content or b""
        if self._metrics:
            self._metrics.record_network_bytes(len(body))
        return body

    def borrow_session(self) -> "_SessionLease":
        """Borrow a pooled session as a context manager for affinity across multiple GETs."""
        return _SessionLease(self._pool)

    def fetch_with(self, session: requests.Session, url: str, headers: dict[str, str] | None = None) -> bytes:
        """GET using a provided session (affinity)."""
        hdrs = dict(headers or {})
        r: Response = session.get(url, headers=hdrs, timeout=self._timeout, allow_redirects=True)

        if r.status_code in (429, 403):
            ex = Exception("rate limited"); setattr(ex, "status_code", r.status_code); raise ex
        r.raise_for_status()

        body = r.content or b""
        if self._metrics:
            self._metrics.record_network_bytes(len(body))
        return body


class _SessionLease(contextlib.AbstractContextManager[requests.Session]):
    """Context manager that borrows and returns a session from the pool."""
    def __init__(self, pool: SessionPool):
        self._pool = pool
        self._session: requests.Session | None = None
    def __enter__(self) -> requests.Session:
        self._session = self._pool.acquire()
        return self._session
    def __exit__(self, exc_type, exc, tb) -> None:
        if self._session is not None:
            self._pool.release(self._session)
            self._session = None


class StatementsRawcraper(StatementsRawcraperPort):
    """Domain-level scraper that coordinates NSD + 13 pages using an AffinityHttpClient."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        datacleaner: DataCleaner,
        metrics_collector: MetricsCollectorPort,
        http_client: AffinityHttpClient,  # public API only
        worker_pool_executor: WorkerPool,
    ) -> None:
        self._config = config
        self.logger = logger
        self.http_client = http_client
        self.datacleaner = datacleaner
        self._metrics_collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor
        self.time_utils = TimeUtils(config)
        self.endpoint = config.exchange.nsd_endpoint
        self.statements_config = config.statements
        self.fetch_utils = FetchUtils(config, logger)
        self.id_generator = IdGenerator(config=config)

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        return self._metrics_collector

    @property
    def config(self) -> ConfigPort:
        return self._config

    # ---------- Helpers ----------

    def _extract_hash(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one("#hdnHash")
        if element:
            value = element.get("value")
            if isinstance(value, str) and value.strip():
                return value.strip()
        form = soup.select_one("form[action*='Hash=']")
        if form:
            action_url = form.get("action", "")
            match = re.search(r"[?&]Hash=([a-zA-Z0-9_-]+)", str(action_url))
            if match:
                return match.group(1)
        return ""

    def _build_urls(self, row: NsdDTO, items: Sequence[Mapping[str, object]], hash_value: str) -> list[dict[str, str]]:
        nsd_type_map = self.statements_config.nsd_type_map
        doctype_name, doctype_code = nsd_type_map.get(row.nsd_type or "INFORMACOES TRIMESTRAIS", ("ITR", 3))
        result: list[dict[str, str]] = []
        for item in items:
            base_url = (self.statements_config.url_df
                        if str(item.get("grupo", "")).startswith("DFs")
                        else self.statements_config.url_capital)
            params = {
                "Grupo": str(item["grupo"]),
                "Quadro": str(item["quadro"]),
                "NomeTipoDocumento": doctype_name,
                "Empresa": row.company_name,
                "DataReferencia": row.quarter.strftime("%Y-%m-%d") if row.quarter is not None else "",
                "Versao": row.version,
                "CodTipoDocumento": str(doctype_code),
                "NumeroSequencialDocumento": str(row.nsd),
                "NumeroSequencialRegistroCvm": "",
                "CodigoTipoInstituicao": "1",
                "Hash": hash_value,
            }
            for campo in ["informacao", "demonstracao", "periodo"]:
                if item.get(campo) is not None:
                    params[campo.capitalize()] = str(item[campo])
            query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
            full_url = f"{base_url}?{query}"
            result.append({"grupo": str(item.get("grupo", "")), "quadro": str(item.get("quadro", "")), "url": full_url})
        return result

    def _parse_statement_page(self, soup: BeautifulSoup, group: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        if group == "Dados da Empresa":
            thousand = 1
            table = soup.find("div", id="UltimaTabela")
            if isinstance(table, Tag):
                text = table.get_text()
                if "Mil" in text:
                    thousand = 1000

            def value_from(elem_id: str) -> float:
                element = soup.find(id=elem_id)
                if element is None:
                    return 0.0
                value = self.datacleaner.clean_number(element.get_text())
                result = thousand * value
                return result if result is not None else 0.0

            for item in self.statements_config.capital_items:
                rows.append({"account": item["account"], "description": item["description"], "value": value_from(item["elem_id"]) })
            return rows

        thousand = 1
        title_element = soup.find(id="TituloTabelaSemBorda")
        if isinstance(title_element, Tag):
            title = title_element.get_text(strip=True)
            if "Mil" in title:
                thousand = 1000

        table = soup.find("table", id="ctl00_cphPopUp_tbDados")
        if not table:
            return rows

        if isinstance(table, Tag):
            table_rows = table.find_all("tr")
            for row in table_rows:
                cols = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cols) < 3:
                    continue
                if not cols[0] or not cols[0][0].isdigit():
                    continue
                account, account_description, account_value = cols[0], cols[1], cols[2]
                rows.append({"account": account, "description": account_description, "value": (self.datacleaner.clean_number(account_value) or 0.0) * thousand})
        return rows

    # ---------- Use case entrypoint ----------

    def fetch(self, task: WorkerTaskDTO) -> dict[str, Any]:
        """Fetch NSD page to get hash, then fetch the 13 tables with session affinity."""
        row: NsdDTO = task.data
        nsd_url = self.endpoint.format(nsd=row.nsd)

        statements_rows_dto: list[StatementRawDTO] = []
        with self.http_client.borrow_session() as session:
            nsd_bytes = self.http_client.fetch_with(session, nsd_url)
            html = nsd_bytes.decode("utf-8", errors="ignore")
            hash_value = self._extract_hash(html)

            statement_items = self._config.statements.statement_items
            statements_urls = self._build_urls(row, statement_items, hash_value)

            for item in statements_urls:
                attempt = 0
                while True:
                    attempt += 1
                    content = self.http_client.fetch_with(session, item["url"], headers={"Referer": nsd_url})
                    self.metrics_collector.record_network_bytes(len(content))
                    soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")

                    text = soup.get_text()
                    blocked = ("MensagemModal" in text or "acesse este conteúdo pela página principal dos documentos" in text)
                    has_table = bool(soup.find("table", id="ctl00_cphPopUp_tbDados")) or (item["grupo"] == "Dados da Empresa" and soup.find("div", id="UltimaTabela"))
                    if blocked and has_table:
                        time.sleep(self.time_utils.sleep_dynamic(multiplier=attempt))
                    break

                rows = self._parse_statement_page(soup, item["grupo"])  # list[dict]
                quarter = row.quarter.strftime("%Y-%m-%d") if row.quarter else None
                for r in rows:
                    statements_rows_dto.append(StatementRawDTO(
                        nsd=str(row.nsd),
                        company_name=row.company_name,
                        quarter=quarter,
                        version=row.version,
                        grupo=item["grupo"],
                        quadro=item["quadro"],
                        account=r["account"],
                        description=r["description"],
                        value=r["value"],
                    ))

        return {"nsd": row, "statements": statements_rows_dto}
