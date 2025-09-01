from __future__ import annotations
from typing import Iterable, List
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from infrastructure.http.http_client import RequestsAffinityHttpClient

class ScraperStatementRaw(ScraperStatementRawPort):
    """
    Scraper de RAW: apenas busca dados externos e transforma em StatementRawDTO.
    Não deduplica, não faz contas, não persiste, não abre sessão.
    """

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        http_client: RequestsAffinityHttpClient,
    ) -> None:
        self.config = config
        self.logger = logger
        self.http = http_client

    def fetch(self, task: WorkerTaskDTO) -> Iterable[StatementRawDTO]:
        nsd: NsdDTO = task.data  # o WorkerPool injeta worker_id no task; não usamos aqui
        if not isinstance(nsd, NsdDTO):
            return []

        url = self._build_url(nsd)
        html = self._get(url)
        rows = self._parse_html_to_rows(html)

        # transforme cada linha “crua” em StatementRawDTO completo e idempotente
        out: List[StatementRawDTO] = []
        for r in rows:
            out.append(StatementRawDTO(
                nsd=nsd.nsd,
                company_name=nsd.company_name,
                year=self._infer_year(nsd),
                quarter=self._infer_quarter(nsd),            # 1..4 já normalizado pela policy
                version=nsd.version,
                account_code=r.account_code,                 # do HTML/API
                account_family=r.account_family,             # p/ regras 3/4 e 6/7
                amount=r.amount,                             # Decimal
                currency=r.currency,                         # se existir
                source="cvm",                                # exemplo estável
            ))
        return out

    # ---- helpers específicos da sua fonte ----
    def _build_url(self, nsd: NsdDTO) -> str:
        # Ex.: use templates do config
        # return self.config.endpoints.statements_raw.format(nsd=nsd.nsd)
        return f"https://exemplo/cvm/raw?nsd={nsd.nsd}"

    def _get(self, url: str) -> str:
        with self.http.borrow_session() as s:
            body = self.http.fetch_with(s, url, headers=s.headers)
        return body.decode("utf-8")

    def _parse_html_to_rows(self, html: str):
        # TODO: portar o parser legado aqui (XPath/regex/BS4), retornando objetos simples
        # com: account_code, account_family, amount, currency
        raise NotImplementedError("porte o parser legado para _parse_html_to_rows")

    def _infer_year(self, nsd: NsdDTO) -> int:
        # se sua policy já normaliza quarter como datetime do fim de trimestre
        return int(getattr(nsd.quarter, "year", getattr(nsd, "year", 0)))

    def _infer_quarter(self, nsd: NsdDTO) -> int:
        # se a policy já mapeia 3→1, 6→2, 9→3, 12→4, use o valor calculado e guarde 1..4
        qdt = getattr(nsd, "quarter", None)
        m = getattr(qdt, "month", None)
        if m in (3, 6, 9, 12):
            return {3:1, 6:2, 9:3, 12:4}[m]
        return 1
