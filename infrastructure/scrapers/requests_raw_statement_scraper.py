"""Scrapers: low-level HTTP fetcher with caching, and domain-level statements scraper."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, Tag
from requests import Response

# Low-level infra deps
from infrastructure.http.session_pool import SessionPool
from infrastructure.repositories.http_cache_repository import HttpCacheRepository

# Domain deps
from domain.dto import WorkerTaskDTO
from domain.dto.nsd_dto import NsdDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import ConfigPort, LoggerPort, MetricsCollectorPort
from domain.ports.scraper_ports import RawStatementScraperPort
from infrastructure.helpers.data_cleaner import DataCleaner
from infrastructure.helpers.fetch_utils import FetchUtils
from infrastructure.helpers.time_utils import TimeUtils
from infrastructure.utils.id_generator import IdGenerator


class RequestsRawStatementScraper:
    """Fetch raw bytes for a URL using a session pool and persistent cache.

    This class is intentionally minimal so it can be wrapped by rate limiter
    and circuit breaker decorators, and is also imported by infra tests.
    """

    def __init__(
        self,
        pool: SessionPool,
        cache: HttpCacheRepository,
        timeout: tuple[float, float] = (5.0, 20.0),
        logger: LoggerPort | None = None,
        metrics: MetricsCollectorPort | None = None,
    ) -> None:
        self._pool = pool
        self._cache = cache
        self._timeout = timeout
        self._logger = logger
        self._metrics = metrics

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Return the content for ``url`` applying ETag/Last-Modified headers."""
        cached = self._cache.get(url)
        hdrs = dict(headers or {})
        if cached and cached.etag:
            hdrs["If-None-Match"] = cached.etag
        if cached and cached.last_modified:
            hdrs["If-Modified-Since"] = cached.last_modified

        s = self._pool.acquire()
        try:
            r: Response = s.get(url, headers=hdrs, timeout=self._timeout, allow_redirects=True)
        finally:
            self._pool.release(s)

        if r.status_code == 304 and cached and cached.body is not None:
            if self._logger:
                self._logger.log("http 304 served from cache", level="info")
            return cached.body

        if r.status_code in (429, 403):
            ex = Exception("rate limited")
            setattr(ex, "status_code", r.status_code)
            raise ex

        r.raise_for_status()

        body = r.content or b""
        self._cache.upsert(
            url,
            etag=r.headers.get("ETag"),
            last_modified=r.headers.get("Last-Modified"),
            body=body,
        )
        if self._metrics:
            self._metrics.record_network_bytes(len(body))
        return body


class RawStatementScraper(RawStatementScraperPort):
    """Domain-level scraper that uses an HTTP client to collect and parse statements."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        data_cleaner: DataCleaner,
        metrics_collector: MetricsCollectorPort,
        http_client,  # must have .fetch(url: str, headers: dict | None) -> bytes
    ) -> None:
        self._config = config
        self.logger = logger
        self.data_cleaner = data_cleaner
        self._metrics = metrics_collector
        self.http = http_client

        self.fetch_utils = FetchUtils(config, logger)
        self.time_utils = TimeUtils(config)
        self.endpoint = config.exchange.nsd_endpoint
        self.statements_config = config.statements
        self.id_generator = IdGenerator(config=config)

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        return self._metrics

    @property
    def config(self) -> ConfigPort:
        return self._config

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

    def _build_urls(
        self, row: NsdDTO, items: Sequence[Mapping[str, object]], hash_value: str
    ) -> list[dict[str, str]]:
        nsd_type_map = self.statements_config.nsd_type_map
        doctype_name, doctype_code = nsd_type_map.get(
            row.nsd_type or "INFORMACOES TRIMESTRAIS",
            ("ITR", 3),
        )
        result: list[dict[str, str]] = []
        for item in items:
            base_url = (
                self.statements_config.url_df
                if str(item.get("grupo", "")).startswith("DFs")
                else self.statements_config.url_capital
            )
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
            result.append(
                {
                    "grupo": str(item.get("grupo", "")),
                    "quadro": str(item.get("quadro", "")),
                    "url": full_url,
                }
            )
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
                value = self.data_cleaner.clean_number(element.get_text())
                result = thousand * value
                return result if result is not None else 0.0

            for item in self.statements_config.capital_items:
                rows.append(
                    {
                        "account": item["account"],
                        "description": item["description"],
                        "value": value_from(item["elem_id"]),
                    }
                )
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
                rows.append(
                    {
                        "account": account,
                        "description": account_description,
                        "value": (self.data_cleaner.clean_number(account_value) or 0.0) * thousand,
                    }
                )
        return rows

    def fetch(self, task: WorkerTaskDTO) -> dict[str, Any]:
        """Fetch statement pages for the given NSD and return parsed rows."""
        row: NsdDTO = task.data
        # First request: load NSD page to extract hash
        nsd_url = self.endpoint.format(nsd=row.nsd)
        body = self.http.fetch(nsd_url)
        html = body.decode("utf-8", errors="ignore")
        hash_value = self._extract_hash(html)

        statement_items = self._config.statements.statement_items
        statements_urls = self._build_urls(row, statement_items, hash_value)

        statements_rows_dto: List[RawStatementDTO] = []
        for i, item in enumerate(statements_urls):
            attempt = 0
            while True:
                attempt += 1
                content = self.http.fetch(item["url"])
                self._metrics.record_network_bytes(len(content))
                soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
                blocked = (
                    "MensagemModal" in soup.get_text()
                    or "acesse este conteúdo pela página principal dos documentos" in soup.get_text()
                )
                if not blocked:
                    break
                # Blocked: backoff and retry
                time.sleep(self.time_utils.get_dynamic_sleep(attempt))

            rows = self._parse_statement_page(soup, item["grupo"])
            quarter = row.quarter.strftime("%Y-%m-%d") if row.quarter else None
            for r in rows:
                dto = RawStatementDTO(
                    nsd=row.nsd,
                    company_name=row.company_name,
                    quarter=quarter,
                    version=row.version,
                    grupo=item["grupo"],
                    quadro=item["quadro"],
                    account=r["account"],
                    description=r["description"],
                    value=r["value"],
                )
                statements_rows_dto.append(dto)

        return {"nsd": row, "statements": statements_rows_dto}
