from __future__ import annotations
from datetime import date
from typing import Optional

from application.usecases.sync_nsd import SyncNSDUseCase
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UnitOfWorkFactoryPort

from domain.dtos.nsd_dto import NsdDTO
from domain.dtos import WorkerTaskDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.polices.nsd_policy_port import NsdPolicyPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort


class NsdService:
    """Camada de aplicação: orquestra fluxo incremental com commit por NSD."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,

        company_repository: RepositoryCompanyDataPort,
        nsd_repository: RepositoryNsdPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,


        company_scraper: ScraperCompanyDataPort,
        nsd_scraper: ScraperNsdPort,
        statements_raw_scraper: ScraperStatementRawPort,

        policy: NsdPolicyPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
        uow_factory: UnitOfWorkFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger

        self.nsd_repository = nsd_repository
        self.company_repository = company_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository

        self.nsd_scraper = nsd_scraper
        self.statements_raw_scraper = statements_raw_scraper

        self.policy = policy
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator
        self.uow_factory = uow_factory

        # stream incremental de NSDs, sem persistir nada aqui
        self.sync_nsd_usecase = SyncNSDUseCase(
            config=config,
            logger=logger,
            nsd_repository=nsd_repository,
            company_repository=company_repository,
            scraper=nsd_scraper,
        )

    def sync_nsd(self, *, start: int = 1, max_nsd: Optional[int] = None) -> None:
        """Processa NSDs incrementalmente com commit atômico por NSD."""
        for nsd in self.sync_nsd_usecase.stream_nsd(start=start, max_nsd=max_nsd):
            self._process_one_nsd(nsd)

    def _process_one_nsd(self, nsd: NsdDTO) -> None:
        supported = self.policy.identify_type(nsd)
        if not supported.supported:
            # caso não suportado: persiste só o NSD e segue a vida
            with self.uow_factory() as uow:
                self.nsd_repository.save_all([nsd], uow=uow)
                uow.commit()
            return

        q = self.policy.normalize_quarter(nsd)
        when = getattr(
            nsd, "date", date(q.year, 12 if q.quarter == 4 else q.quarter * 3, 1)
            )
        r = self.policy.compute_recency_window(when)
        action = self.policy.decide_action(
            year=q.year,
            quarter=q.quarter,
            version=nsd.version,
            is_december=q.is_december,
            is_recent=r.is_recent,
        )

        # Wrap the NsdDTO in a WorkerTaskDTO as required by the port.
        # The 'index' and 'worker_id' can be placeholders if not needed immediately.
        task = WorkerTaskDTO(index=0, data=nsd, worker_id="main_thread")
        
        self.logger.log(f'MISSING IMPLEMENTATION: {task}')
        # Pass to the fetch method.
        # raw_lines = self.raw_scraper.fetch(task)

        # if action.is_raw():
        #     # commit inclui RAW + NSD, juntos
        #     with self.uow_factory() as uow:
        #         self.raw_repo.upsert_bulk(raw_lines, uow)
        #         self.nsd_repository.upsert(nsd, uow)
        #         uow.commit()
        #     return

        # # PROCESS: resolve visão do ano no repositório de RAW, dedup de versões,
        # # normaliza e calcula ratios; commit inclui RAW + FETCHED + NSD
        # company_id = self._company_for(nsd)
        # year_view = self.raw_repo.get_company_year_view(company_id=company_id, year=q.year)
        # deduped = self.policy.version_deduplicate(tuple(year_view) + tuple(raw_lines))
        # standardized = self.normalizer.standardize(deduped)
        # fetched = self.ratios.calculate(standardized)
        # processing_hash = self._hash_run(deduped, standardized, fetched)

        # with self.uow_factory() as uow:
        #     self.raw_repo.upsert_bulk(raw_lines, uow)
        #     self.fetched_repo.upsert_bulk(fetched, processing_hash, uow)
        #     self.nsd_repository.upsert(nsd, uow)
        #     uow.commit()

    def _company_for(self, nsd: NsdDTO) -> str:
        return self.company_repository.get_id_by_name(nsd.company_name)

    def _hash_run(self, *parts) -> str:
        import hashlib, json
        blob = json.dumps([self._to_primitive(p) for p in parts], sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _to_primitive(self, obj):
        if isinstance(obj, (list, tuple)):
            return [self._to_primitive(x) for x in obj]
        if hasattr(obj, "__dict__"):
            return {k: self._to_primitive(v) for k, v in obj.__dict__.items()}
        return obj
