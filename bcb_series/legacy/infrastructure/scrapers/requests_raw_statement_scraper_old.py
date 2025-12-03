"""Statement source adapter for fetching financial reports."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Mapping, Sequence
from urllib.parse import quote_plus

# import pandas as pd
from bs4 import BeautifulSoup, Tag

from domain.dto import WorkerTaskDTO
from domain.dto.nsd_dto import NsdDTO
from domain.dto.statement_raw_dto import StatementRawDTO
from domain.ports import ConfigPort, LoggerPort, MetricsCollectorPort
from domain.ports.scraper_ports import StatementsRawcraperPort
from infrastructure.adapters.sqlalchemy_engine_mixin import SqlAlchemyEngineMixin
from infrastructure.helpers import WorkerPool
from infrastructure.helpers.datacleaner import DataCleaner
from infrastructure.helpers.fetch_utils import FetchUtils
from infrastructure.helpers.time_utils import TimeUtils
from infrastructure.utils.id_generator import IdGenerator


class StatementsRawcraper(SqlAlchemyEngineMixin, StatementsRawcraperPort):
    """Fetch statement HTML using ``requests``."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        datacleaner: DataCleaner,
        metrics_collector: MetricsCollectorPort,
        worker_pool_executor: WorkerPool,
    ) -> None:
        super().__init__(config.database.connection_string, logger)
        self._config: ConfigPort = config

        # Adapter-specific dependencies
        self.datacleaner = datacleaner
        self._metrics_collector = metrics_collector
        self.worker_pool_executor = worker_pool_executor

        # Utilities for scraping and ID generation
        self.fetch_utils = FetchUtils(config, logger)
        self.time_utils = TimeUtils(config)
        self.session = self.fetch_utils.create_scraper()
        self.endpoint = config.exchange.nsd_endpoint
        self.statements_config = config.statements
        self.id_generator = IdGenerator(config=config)

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""

        return self._metrics_collector

    @property
    def config(self) -> ConfigPort:
        """Return configuration used by the scraper."""

        return self._config

    def _parse_statement_page(
        self, soup: BeautifulSoup, group: str
    ) -> List[Dict[str, Any]]:
        """Return fetched rows from a statement ``soup``."""
        rows: List[Dict[str, Any]] = []

        # Default parsing for Capital Composition page
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
                rows.append(
                    {
                        "account": item["account"],
                        "description": item["description"],
                        "value": value_from(item["elem_id"]),
                    }
                )
            return rows

        # Default parsing for DFs pages
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
                # ignora linhas cujo account não começa com dígito
                if len(cols) < 3:
                    continue
                if not cols[0] or not cols[0][0].isdigit():
                    continue
                account, account_description, account_value = cols[0], cols[1], cols[2]
                rows.append(
                    {
                        "account": account,
                        "description": account_description,
                        "value": (self.datacleaner.clean_number(account_value) or 0.0)
                        * thousand,
                    }
                )

        return rows

    def _extract_hash(self, html: str) -> str:
        """Extract the hidden hash value from the HTML response."""
        soup = BeautifulSoup(html, "html.parser")
        # hash in element
        element = soup.select_one("#hdnHash")
        if element:
            value = element.get("value")
            if isinstance(value, str) and value.strip():
                return value.strip()

        # hash in form
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
        """Construct statement URLs using ``row`` data and the given hash."""
        nsd_type_map = self.statements_config.nsd_type_map

        doctype_name, doctype_code = nsd_type_map.get(
            row.nsd_type or "INFORMACOES TRIMESTRAIS",
            ("ITR", 3),
        )

        result: list[dict[str, str]] = []

        try:
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
                    "DataReferencia": row.quarter.strftime("%Y-%m-%d")
                    if row.quarter is not None
                    else "",
                    "Versao": row.version,
                    "CodTipoDocumento": str(doctype_code),
                    "NumeroSequencialDocumento": str(row.nsd),
                    "NumeroSequencialRegistroCvm": "",  # hardcoded
                    "CodigoTipoInstituicao": "1",  # hardcoded
                    "Hash": hash_value,
                }

                # Inclui os parâmetros extras (se presentes)
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
        except Exception as e:
            print(e)
        return result

    def fetch(self, task: WorkerTaskDTO) -> dict[str, Any]:
        """Fetch statement pages for the given NSD and return fetched rows."""
        # self.logger.log("Run  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().processor().source.fetch()", level="info")
        row = task.data

        url = self.endpoint.format(nsd=row.nsd)
        start = time.perf_counter()

        response, self.session = self.fetch_utils.fetch_with_retry(
            self.session, url, cache_bypass=True
        )

        download = len(response.content)
        self.metrics_collector.record_network_bytes(download)

        hash_value = self._extract_hash(response.text)

        statement_items = self.config.domain.statement_items
        statements_urls = self._build_urls(row, statement_items, hash_value)

        # Parse all statement pages
        statements_rows_dto: List[StatementRawDTO] = []

        # for i, item in enumerate(statements_urls):
        for i in range(len(statements_urls)):
            item = statements_urls[i]

            quarter = row.quarter.strftime("%Y-%m-%d") if row.quarter else None
            attempt = 0
            # loop infinito até conseguir um response não bloqueado
            while True:
                attempt += 1
                # 1) tentativa de fetch
                response, self.session = self.fetch_utils.fetch_with_retry(
                    self.session,
                    url=item["url"],
                    cache_bypass=True,
                    worker_id=worker_id,
                )
                # 2) registra bytes baixados
                download = len(response.content)
                self.metrics_collector.record_network_bytes(download)

                # 3) parse do HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # 4) checa se houve bloqueio
                blocked = (
                    "MensagemModal" in response.text
                    or "acesse este conteúdo pela página principal dos documentos"
                    in soup.get_text()
                )

                if not blocked:
                    # Sucesso: podemos sair do loop
                    # self.logger.log(
                    #     f"{row.nsd} {row.company_name} {quarter} {row.version} - {i} {item['grupo']} {item['quadro']}",
                    #     level="info",
                    #     worker_id=task.worker_id,
                    # )
                    break

                # --- caso de bloqueio: prepara nova tentativa ---
                # 5) recria a sessão (novo scraper)
                self.session = self.fetch_utils.create_scraper()

                # 6) faz um novo fetch para extrair o hash atualizado
                response_retry, self.session = self.fetch_utils.fetch_with_retry(
                    self.session, url, cache_bypass=True
                )
                download = len(response_retry.content)
                self.metrics_collector.record_network_bytes(download)

                # 7) extrai novo hash
                hash_retry_value = self._extract_hash(response_retry.text)

                # 8) reconstrói as URLs de statements
                if hash_value != hash_retry_value:
                    statements_urls = self._build_urls(
                        row, statement_items, hash_retry_value or hash_value
                    )
                    item = statements_urls[i]

                # self.logger.log(
                #     f"{row.nsd} {row.company_name} {quarter} {row.version} - {i} {item['grupo']} {item['quadro']} retry {attempt}",
                #     level="warning",
                #     worker_id=task.worker_id
                # )

                # 8) espera dinamicamente, aumentando o multiplicador a cada retry
                self.time_utils.sleep_dynamic(multiplier=attempt)
                # e repete até obter sucesso

            # A partir daqui, `response` e `item` já estão válidos (não bloqueados)
            result: dict[str, Any] = {"nsd": row, "statements": []}

            rows = self._parse_statement_page(soup, item["grupo"])
            fetched_rows = []

            for r in rows:
                dto = StatementRawDTO(
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
                fetched_rows.append(dto)

            statements_rows_dto.extend(fetched_rows)

        _elapsed = time.perf_counter() - start
        quarter = row.quarter.strftime("%Y-%m-%d") if row.quarter else None
        # self.logger.log(
        #     f"{row.nsd} {row.company_data_name} {quarter} {row.version} in {elapsed:.2f}s",
        #     level="info",
        # )
        result = {"nsd": row, "statements": statements_rows_dto}

        # self.logger.log("End  Method controller.run()._statement_service().statements_fetch_service.run().fetch_usecase.run().fetch_all().processor().source.fetch()", level="info")

        return result
