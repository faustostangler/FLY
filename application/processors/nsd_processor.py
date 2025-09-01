from __future__ import annotations
from datetime import date, datetime
import time
from typing import Optional

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


class _NsdTxnAggregator:
    """Mantém NSD, RAW e FETCHED juntos para flush atômico."""
    def __init__(self, *, nsd_repository, statements_raw_repository, statements_fetched_repository):
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository
        self._nsd: Optional[NsdDTO] = None
        self._raw = []
        self._fetched = []

    def set_nsd(self, nsd: NsdDTO) -> None:
        self._nsd = nsd

    def add_raw_many(self, items) -> None:
        self._raw.extend(items)

    def add_fetched_many(self, items) -> None:
        self._fetched.extend(items)

    def flush(self, *, uow: Uow) -> None:
        if self._raw:
            self.statements_raw_repository.save_all(self._raw, uow=uow)
        if self._fetched:
            self.statements_fetched_repository.save_all(self._fetched, uow=uow)
        if self._nsd is not None:
            self.nsd_repository.save_all([self._nsd], uow=uow)

        self._nsd = None
        self._raw.clear()
        self._fetched.clear()


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
    def __call__(self, task: WorkerTaskDTO) -> NsdDTO:
        return self.run(task)

    def run(self, task: WorkerTaskDTO) -> NsdDTO:
        data = task.data
        data = 10008
        nsd = NsdDTO(id=None, nsd=10008, company_name='IND MAQS AGRICOLAS FUCHS SA', quarter=datetime(2011, 3, 31, 0, 0), version=1, nsd_type='INFORMACOES TRIMESTRAIS', dri='JALMAR JOSE MARTEL', auditor='MULTICON AUDITORIA E ASSESSORIA CONTABIL SS', responsible_auditor='MARCO ANTONIO PALERMO', protocol='007064ITR310320110100010008-86', sent_date=datetime(2011, 7, 6, 22, 1, 35), reason=None)

        # start_time = time.perf_counter()
        # nsd = self.scraper_nsd.fetch_one(int(data))

        if nsd is None:
            self.logger.log(f"NSD not found: {data}", level="info")
            return task.data

        with self.uow_factory() as uow:
            self._ensure_company_exists(nsd.company_name, uow=uow)
            nsd_type = self.policy.identify_type(nsd)

            agg = _NsdTxnAggregator(
                nsd_repository=self.nsd_repository,
                statements_raw_repository=self.statements_raw_repository,
                statements_fetched_repository=self.statements_fetched_repository,
            )

            if not nsd_type.is_statement:
                agg.set_nsd(nsd)
                agg.flush(uow=uow)
                uow.commit()

                progress = {
                    "index": task.index,
                    "size": 100000,  # len(tasks),
                    "start_time": start_time,
                }
                extra_info = [ f"{nsd.nsd} {nsd.quarter} | {nsd.sent_date} v{nsd.version} | {nsd.nsd_type} {nsd.company_name}"]
                self.logger.log(
                    f"{nsd.nsd}",
                    level="info",
                    progress={**progress, "extra_info": extra_info},
                    worker_id=task.worker_id,
                )

                return nsd

            q = self.policy.normalize_quarter(nsd)
            sd = getattr(nsd, "sent_date")
            if hasattr(sd, "date"):
                sd = sd.date()
            when = sd or date(q.year, q.quarter * 3, 1)
            recency = self.policy.compute_recency_window(when)
            action = self.policy.decide_action(
                year=q.year, quarter=q.quarter, version=nsd.version,
                is_december=q.is_december, is_recent=recency.is_recent,
            )

            raw_lines = list(self.scraper_statements_raw.fetch(nsd))

            if action.is_raw():
                agg.add_raw_many(raw_lines)
                agg.set_nsd(nsd)
                agg.flush(uow=uow)
                uow.commit()
                self.logger.log(
                    f"Processed NSD_RAW NSD: {nsd.nsd} {nsd.quarter} {nsd.sent_date} v{nsd.version} {nsd.nsd_type} {nsd.company_name}",
                    level="info",
                )
                return nsd

            # PROCESS
            company_id = self.company_repository.get_cvm_by_name(nsd.company_name, uow=uow)
            year_view = list(
                self.statements_raw_repository.get_company_year_view(company_id=company_id, year=q.year, uow=uow)
            )
            deduped = self.policy.version_deduplicate(tuple(year_view) + tuple(raw_lines))
            standardized = self.financial_normalizer.standardize(deduped)
            fetched = self.ratios_calculator.calculate(standardized)

            agg.add_raw_many(raw_lines)
            agg.add_fetched_many(list(fetched))
            agg.set_nsd(nsd)
            agg.flush(uow=uow)
            uow.commit()

            self.logger.log(
                f"Processed NSD_RAW_FETCHED NSD: {nsd.nsd} {nsd.quarter} {nsd.sent_date} v{nsd.version} {nsd.nsd_type} {nsd.company_name}",
                level="info",
            )
            return nsd

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
