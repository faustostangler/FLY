from __future__ import annotations
from typing import Iterable, List, Dict, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup, Tag

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from infrastructure.http.http_client import RequestsAffinityHttpClient


class ScraperStatementRaw(ScraperStatementRawPort):
    """
    Scraper de RAW: busca as páginas de demonstrações de um NSD e devolve StatementRawDTO.
    Não deduplica, não calcula, não persiste.
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
        # endpoints esperados em config:
        # - exchange.nsd_endpoint (página principal do NSD que contém o hash)
        # - statements.url_df (páginas de DFs)
        # - statements.url_capital (página de “Dados da Empresa”)
        # - statements.statement_items (lista de dicts com "grupo", "quadro" e extras)
        # - statements.nsd_type_map (mapeia nsd_type → (NomeTipoDocumento, CodTipoDocumento))

    # API pública
    def fetch(self, nsd: NsdDTO) -> Iterable[StatementRawDTO]:
        # 1) baixa página do NSD e extrai hash
        nsd_url = self.config.exchange.nsd_endpoint.format(nsd=nsd.nsd)
        html = self._get(nsd_url)
        hdn_hash = self._extract_hash(html)

        # 2) monta a lista de URLs por grupo/quadro
        items = self.config.domain.statement_items
        urls = self._build_urls(nsd, items, hdn_hash)

        # 3) para cada URL, baixa e parseia linhas
        out: List[StatementRawDTO] = []
        for item in urls:
            page_html = self._get(item["url"])
            rows = self._parse_statement_page(BeautifulSoup(page_html, "html.parser"), item["grupo"])

            # 4) converte linhas para DTOs idempotentes
            year, quarter = self._infer_year_quarter(nsd)
            for r in rows:
                out.append(
                    StatementRawDTO(
                        nsd=str(nsd.nsd),
                        company_name=nsd.company_name,
                        year=year,
                        quarter=quarter,            # 1..4
                        version=int(nsd.version),
                        grupo=item["grupo"],
                        quadro=item["quadro"],
                        account=r["account"],
                        description=r["description"],
                        value=r["value"],
                    )
                )
        return out

    # ---------- helpers legado-essência ----------

    def _get(self, url: str) -> str:
        with self.http.borrow_session() as s:
            body = self.http.fetch_with(s, url, headers=s.headers)
        return body.decode("utf-8")

    def _extract_hash(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one("#hdnHash")
        if el is None:
            raise ValueError("Elemento '#hdnHash' não encontrado")
        v = el.get("value")
        if isinstance(v, list):
            v = v[0] if v else ""
        if not isinstance(v, str):
            raise ValueError("Valor inválido para 'value'")
        return v

    def _build_urls(self, row: NsdDTO, items: list, hash_value: str) -> list[dict[str, str]]:
        name, code = self.config.statements.nsd_type_map.get(
            row.nsd_type or "INFORMACOES TRIMESTRAIS", ("ITR", 3)
        )

        result: list[dict[str, str]] = []
        for it in items:
            base = self.config.statements.url_df if it["grupo"].startswith("DFs") else self.config.statements.url_capital
            params = {
                "Grupo": it["grupo"],
                "Quadro": it["quadro"],
                "NomeTipoDocumento": name,
                "Empresa": row.company_name,
                "DataReferencia": row.quarter.strftime("%Y-%m-%d") if row.quarter else "",
                "Versao": row.version,
                "CodTipoDocumento": str(code),
                "NumeroSequencialDocumento": str(row.nsd),
                "NumeroSequencialRegistroCvm": "",
                "CodigoTipoInstituicao": "1",
                "Hash": hash_value,
            }
            for k in ("informacao", "demonstracao", "periodo"):
                if it.get(k) is not None:
                    params[k.capitalize()] = str(it[k])
            query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
            result.append({"grupo": it["grupo"], "quadro": it["quadro"], "url": f"{base}?{query}"})
        return result

    def _parse_statement_page(self, soup: BeautifulSoup, group: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        if group == "Dados da Empresa":
            thousand = 1
            table = soup.find("div", id="UltimaTabela")
            if isinstance(table, Tag):
                if "Mil" in table.get_text():
                    thousand = 1000

            def val(elem_id: str) -> float:
                el = soup.find(id=elem_id)
                if el is None:
                    return 0.0
                txt = el.get_text()
                num = self._clean_number(txt)
                return float(num or 0.0) * thousand

            for item in self.config.statements.capital_items:
                rows.append(
                    {
                        "account": item["account"],
                        "description": item["description"],
                        "value": val(item["elem_id"]),
                    }
                )
            return rows

        thousand = 1
        title = soup.find(id="TituloTabelaSemBorda")
        if isinstance(title, Tag):
            if "Mil" in title.get_text(strip=True):
                thousand = 1000

        table = soup.find("table", id="ctl00_cphPopUp_tbDados")
        if not isinstance(table, Tag):
            return rows

        for tr in table.find_all("tr"):
            cols = [c.get_text(strip=True) for c in tr.find_all("td")]
            if len(cols) < 3:
                continue
            if not cols[0] or not cols[0][0].isdigit():
                continue
            account, desc, valtxt = cols[0], cols[1], cols[2]
            num = self._clean_number(valtxt)
            rows.append(
                {
                    "account": account,
                    "description": desc,
                    "value": float(num or 0.0) * thousand,
                }
            )
        return rows

    def _clean_number(self, s: str) -> Optional[float]:
        # limpeza simples: remove separadores PT-BR e converte
        if s is None:
            return None
        txt = s.replace(".", "").replace("\xa0", "").replace(" ", "").replace("R$", "").replace("%", "")
        txt = txt.replace(",", ".")
        try:
            return float(txt)
        except Exception:
            return None

    def _infer_year_quarter(self, nsd: NsdDTO) -> tuple[int, int]:
        # supõe que policy já normalizou quarter como fim de trimestre: 31/03, 30/06, 30/09, 31/12
        y = int(getattr(nsd.quarter, "year", getattr(nsd, "year", 0)))
        m = int(getattr(nsd.quarter, "month", getattr(nsd, "month", 3)))
        q = {3: 1, 6: 2, 9: 3, 12: 4}.get(m, 1)
        return y, q
