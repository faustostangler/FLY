from __future__ import annotations
from datetime import date
from typing import Iterable, Optional

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from infrastructure.utils.id_generator import IdGenerator
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.polices.nsd_policy import NsdPolicyPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from domain.ports.scraper_nsd_port import ScraperNsdPort

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
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator

        self.id_generator = IdGenerator(config=config)

    # compat com pools que chamam .run(task) ou chamam o objeto
    def __call__(self, task: WorkerTaskDTO) -> None:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> None:
        data = task.data
        nsd = data if isinstance(data, NsdDTO) else self.scraper_nsd.fetch_one(int(data))
        if nsd is None:
            self.logger.log(f"NSD not found: {data}", level="info")
            return
        with self.uow_factory() as uow:
            self._ensure_company_exists(nsd.company_name, uow=uow)
            nsd_type = self.policy.identify_type(nsd)
            if not nsd_type.is_statement:
                self.nsd_repository.save_all([nsd], uow=uow)
                uow.commit()
                self._log_done(nsd, tag="NSD_ONLY")
                return
            q = self.policy.normalize_quarter(nsd)
            sd = getattr(nsd, "sent_date", None)
            if hasattr(sd, "date"):
                sd = sd.date()
            when = sd or date(q.year, q.quarter * 3, 1)
            rec = self.policy.compute_recency_window(when)
            action = self.policy.decide_action(
                year=q.year, quarter=q.quarter, version=nsd.version,
                is_december=q.is_december, is_recent=rec.is_recent,
            )
            if not action.kind == "RAW":
                pass
            # raw_lines = list(self.scraper_statements_raw.fetch(task))
            # if action.is_raw():
            #     self.statements_raw_repository.save_all(raw_lines, uow=uow)
            #     self.nsd_repository.save_all([nsd], uow=uow)
            #     uow.commit()
            #     self._log_done(nsd, tag="RAW")
            #     return
            # company_id = self.company_repository.get_cvm_by_name(nsd.company_name, uow=uow)
            # year_view = list(self.statements_raw_repository.get_company_year_view(company_id=company_id, year=q.year, uow=uow))
            # deduped = self.policy.version_deduplicate(tuple(year_view) + tuple(raw_lines))
            # standardized = self.financial_normalizer.standardize(deduped)
            # fetched = self.ratios_calculator.calculate(standardized)
            # self.statements_raw_repository.save_all(raw_lines, uow=uow)
            # self.statements_fetched_repository.save_all(list(fetched), uow=uow)
            # self.nsd_repository.save_all([nsd], uow=uow)
            # uow.commit()
            # self._log_done(nsd, tag="PROCESS")

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
        import hashlib, json
        def to_prim(obj):
            if isinstance(obj, (list, tuple)):
                return [to_prim(x) for x in obj]
            if hasattr(obj, "__dict__"):
                return {k: to_prim(v) for k, v in obj.__dict__.items()}
            return obj
        blob = json.dumps([to_prim(p) for p in parts], sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _log_done(self, nsd: NsdDTO, *, tag: str) -> None:
        self.logger.log(
            f"Processed {tag} NSD: {nsd.nsd} {nsd.quarter} {nsd.sent_date} v{nsd.version} {nsd.nsd_type} {nsd.company_name}",
            level="info",
        )
