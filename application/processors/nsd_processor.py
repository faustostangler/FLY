from __future__ import annotations

import time
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Set, cast

from application.ports.market_data_port import MarketDataPort
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.polices.nsd_policy import NsdPolicyPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from application.services.market_data_service import MarketDataService
from infrastructure.repositories.market_quote_repository import MarketQuoteRepository
from infrastructure.utils.id_generator import IdGenerator


class _NsdTxnAggregator:
    """Mantém NSD, RAW e FETCHED juntos para flush atômico."""
    def __init__(self, *, nsd_repository, statements_raw_repository, statements_fetched_repository):
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self._nsd_data: Optional[NsdDTO] = None
        self._raw_data = []
        self._fetched_data = []

    def set_nsd(self, nsd: NsdDTO) -> None:
        self._nsd_data = nsd

    def add_raw_many(self, items) -> None:
        self._raw_data.extend(items)

    def add_fetched_many(self, items) -> None:
        self._fetched_data.extend(items)

    def flush(self, *, uow: Uow) -> None:
        if self._nsd_data is not None:
            self.nsd_repository.save_all([self._nsd_data], uow=uow)
        if self._raw_data:
            self.statements_raw_repository.save_all(self._raw_data, uow=uow)
        if self._fetched_data:
            self.statements_fetched_repository.save_all(self._fetched_data, uow=uow)

        self._nsd_data = None
        self._raw_data.clear()
        self._fetched_data.clear()


class NsdProcessor:
    """Processa 1 NSD por vez. Cada tarefa abre sua própria UoW."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,

        nsd_repository: RepositoryNsdPort,
        company_repository: RepositoryCompanyDataPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,

        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,

        policy: NsdPolicyPort,
        market_data_port: MarketDataPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger

        self.company_repository = company_repository
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self.scraper_statements_raw = scraper_statements_raw

        self.scraper_nsd = scraper_nsd

        self.uow_factory = uow_factory
        self.policy = policy
        self.market_data_port = market_data_port
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator

        self.id_generator = IdGenerator(config=config)

    # compat com pools que chamam .run(task) ou chamam o objeto
    def __call__(self, task: WorkerTaskDTO) -> NsdDTO:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> NsdDTO:
        data = task.data
        # data = 82408  
        # nsd = NsdDTO(id=None, nsd=10012, company_name='IND MAQS AGRICOLAS FUCHS SA', quarter=datetime.datetime(2011, 3, 31, 0, 0), version=2, nsd_type='INFORMACOES TRIMESTRAIS', dri='JALMAR JOSE MARTEL', auditor='MULTICON AUDITORIA E ASSESSORIA CONTABIL SS', responsible_auditor='MARCO ANTONIO PALERMO', protocol='007064ITR310320110200010012-79', sent_date=datetime.datetime(2011, 7, 7, 11, 7, 36), reason='AS INFORMACOES NO RELATORIO DA REVISAO ESPECIAL NAO SE REFEREM AO TRIMESTRE EM QUESTAO E SIM SOBRE O MESMO PERIODO POREM DO EXERCICIO ANTERIOR E QUE AGORA ESTAMOS TRANSCREVENDO O CONTEUDO CORRETO')

        start_time = time.perf_counter()
        nsd = self.scraper_nsd.fetch_one(int(data))
        progress = {
            "index": task.index,
            "size": task.total_size,
            "start_time": start_time,
        }

        if nsd is None:
            extra_info = [ f""]
            self.logger.log(
                f"NSD {data}",
                level="info",
                progress={**progress, "extra_info": extra_info},
                worker_id=task.worker_id,
            )
            return task.data

        with self.uow_factory() as uow:
            self._ensure_company_exists(nsd.company_name, uow=uow)
            nsd_type = self.policy.identify_type(nsd)

            agg = _NsdTxnAggregator(
                nsd_repository=self.nsd_repository,
                statements_raw_repository=self.statements_raw_repository,
                statements_fetched_repository=self.statements_fetched_repository,
            )

            nsd_quarter = nsd.quarter.strftime("%Y-%m-%d") if isinstance(nsd.quarter, datetime) else (nsd.quarter or "")
            extra_info = [ f"{nsd.nsd} {nsd_quarter} | {nsd.sent_date} v{nsd.version} | {nsd.nsd_type} {nsd.company_name}"]
            self.logger.log(
                f"NSD {nsd.nsd}",
                level="info",
                progress={**progress, "extra_info": extra_info},
                worker_id=task.worker_id,
            )

            if not nsd_type.is_statement:
                agg.set_nsd(nsd)
                agg.flush(uow=uow)
                uow.commit()

                return nsd

            quarter_police = self.policy.normalize_quarter(nsd)
            sd = getattr(nsd, "sent_date")
            if hasattr(sd, "date"):
                sd = sd.date()
            when = sd or date(quarter_police.year, quarter_police.month, 1)
            recency = self.policy.compute_recency_window(when)
            action = self.policy.decide_action(
                year=quarter_police.year, quarter=quarter_police.month, version=nsd.version,
                is_december=quarter_police.is_december, is_recent=recency.is_recent,
            )

            # raw_lines = list(self.scraper_statements_raw.fetch(nsd))
            raw_result  = self.scraper_statements_raw.fetch(
                WorkerTaskDTO(
                    index=task.index,
                    data=nsd,
                    worker_id=task.worker_id,
                    total_size=task.total_size,
                )
            )
            raw_lines = list(raw_result["items"])

            nsd_quarter = nsd.quarter.strftime("%Y-%m-%d") if isinstance(nsd.quarter, datetime) else (nsd.quarter or "")
            extra_info = [ f"{nsd.nsd} {nsd_quarter} | {nsd.sent_date} v{nsd.version} | {nsd.nsd_type} {nsd.company_name}"]
            self.logger.log(
                f"RAW {nsd.nsd}",
                level="info",
                progress={**progress, "extra_info": extra_info},
                worker_id=task.worker_id,
            )

            # from dataclasses import asdict
            # import pandas as pd
            # from pathlib import Path

            # # salvar
            # path = Path("raw_lines.csv")
            # pd.DataFrame([asdict(x) for x in raw_lines]).to_csv(path, index=False, encoding="utf-8")

            # # ler
            # from pathlib import Path
            # import pandas as pd
            # path = Path("raw_lines.csv")
            # df = pd.read_csv(path, encoding="utf-8")
            # from dataclasses import fields
            # from domain.dtos.statement_raw_dto import StatementRawDTO  # ajuste o import

            # cols = [f.name for f in fields(StatementRawDTO)]
            # raw_lines = []
            # for _, row in df[cols].iterrows():
            #     raw_lines.append(
            #         StatementRawDTO(
            #             nsd=str(row["nsd"]),
            #             company_name=str(row["company_name"]),
            #             quarter=row["quarter"],
            #             version=row["version"],
            #             grupo=str(row["grupo"]),
            #             quadro=str(row["quadro"]),
            #             account=str(row["account"]),
            #             description=str(row["description"]),
            #             value=float(row["value"]),
            #         )
            #     )
            

            if action.is_raw():
                agg.add_raw_many(raw_lines)
                agg.set_nsd(nsd)
                agg.flush(uow=uow)
                uow.commit()
                return nsd
            try:
                # PROCESS
                # company_id = self.company_repository.get_cvm_by_name(nsd.company_name, uow=uow)
                year_view = list(
                    self.statements_raw_repository.get_company_year_view(
                        company_name=nsd.company_name,
                        year=quarter_police.year,
                        uow=uow,
                    )
                )

                combined: List[StatementRawDTO] = list(year_view) + list(raw_lines)
                deduped = self.policy.version_deduplicate(combined)
                quarterized = self.financial_normalizer.quarterize(deduped)
                standardized = self.financial_normalizer.standardize(quarterized)

                # market data
                market_repo = MarketQuoteRepository(uow.session)
                market_service = MarketDataService(self.market_data_port, market_repo)

                by_company: Dict[tuple[str, str], Set[date]] = defaultdict(set)

                for s in standardized:
                    company = s.company_name
                    if not company:
                        continue
                    quarter = s.quarter
                    if quarter is None:
                        continue
                    if isinstance(quarter, datetime):
                        q_end = quarter.date()
                    elif isinstance(quarter, date):
                        q_end = quarter
                    else:
                        try:
                            q_end = date.fromisoformat(str(quarter).split(" ")[0])
                        except Exception:
                            continue
                    by_company[(s.nsd, company)].add(q_end)

                symbol_cache: Dict[tuple[str, str], Optional[str]] = {}

                def resolve_symbol(nsd_code: str, company: str) -> Optional[str]:
                    key = (nsd_code, company)
                    if key not in symbol_cache:
                        symbol_cache[key] = self.company_repository.get_market_symbol(
                            nsd_code,
                            company,
                            uow=uow,
                        )
                    return symbol_cache[key]

                for (nsd_code, company), quarter_ends in by_company.items():
                    symbol = resolve_symbol(nsd_code, company)
                    if not symbol:
                        continue
                    market_service.ensure_series_for_quarters(symbol, quarter_ends)

                def price_lookup(nsd_code: str, company: str, quarter_end: date):
                    symbol = resolve_symbol(nsd_code, company)
                    if not symbol:
                        return None
                    when = quarter_end
                    if isinstance(when, datetime):
                        when = when.date()
                    elif not isinstance(when, date):
                        try:
                            when = date.fromisoformat(str(when).split(" ")[0])
                        except Exception:
                            return None
                    return market_service.price_at_quarter_end(symbol, when)

                ratios = self.ratios_calculator.calculate(
                    cast(Sequence[StatementFetchedDTO], standardized),
                    price_lookup=price_lookup,
                )


                ratios = self.ratios_calculator.calculate(cast(Sequence[StatementFetchedDTO], standardized))
                fetched = list(standardized) + list(ratios)

                nsd_quarter = nsd.quarter.strftime("%Y-%m-%d") if isinstance(nsd.quarter, datetime) else (nsd.quarter or "")
                extra_info = [ f"{nsd.nsd} {nsd_quarter} | {nsd.sent_date} v{nsd.version} | {nsd.nsd_type} {nsd.company_name}"]
                self.logger.log(
                    f"FTD {nsd.nsd}",
                    level="info",
                    progress={**progress, "extra_info": extra_info},
                    worker_id=task.worker_id,
                )

                agg.add_raw_many(raw_lines)
                agg.add_fetched_many(list(fetched))
                agg.set_nsd(nsd)
                agg.flush(uow=uow)
                uow.commit()

                return nsd
            except Exception as e:
                self.logger.log(f"{e}")

    def _ensure_company_exists(self, company_name: Optional[str], *, uow: Uow) -> Optional[str]:
        if not company_name:
            return None
        cvm = self.company_repository.get_cvm_by_name(company_name, uow=uow)
        if cvm:
            return cvm
        dto = CompanyDataDTO(
            cvm_code=self.id_generator.create_id(size=6),
            company_name=company_name,
        )
        self.company_repository.save_all([dto], uow=uow)
        return dto.cvm_code

    def _hash_run(self, *parts) -> str:
        import hashlib
        import json

        def to_prim(obj):
            if isinstance(obj, (list, tuple)):
                return [to_prim(x) for x in obj]
            if hasattr(obj, "__dict__"):
                return {k: to_prim(v) for k, v in obj.__dict__.items()}
            return obj

        blob = json.dumps([to_prim(p) for p in parts], sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
