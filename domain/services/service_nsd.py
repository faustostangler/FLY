from __future__ import annotations
from datetime import date
from typing import Optional

from application.usecases.sync_nsd import SyncNSDUseCase
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.uow_port import Uow
from infrastructure.utils.id_generator import IdGenerator

from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.nsd_dto import NsdDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.polices.nsd_policy import NsdPolicyPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.processors.nsd_processor import NsdProcessor


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

        scraper_company_data: ScraperCompanyDataPort,
        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,

        worker_pool: WorkerPoolPort,

        policy: NsdPolicyPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger

        self.nsd_repository = nsd_repository
        self.company_repository = company_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository

        self.scraper_company_data = scraper_company_data
        self.scraper_nsd = scraper_nsd
        self.scraper_statements_raw = scraper_statements_raw

        self.id_generator = IdGenerator(config=config)
        self.worker_pool = worker_pool

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
            scraper=scraper_nsd,
            uow_factory=uow_factory,
        )

        self._processor = NsdProcessor(
            config=config,
            logger=logger,

            nsd_repository=nsd_repository,
            company_repository=company_repository,
            statements_raw_repository=statements_raw_repository,
            statements_fetched_repository=statements_fetched_repository,

            scraper_nsd=scraper_nsd,
            scraper_statements_raw=scraper_statements_raw,

            policy=policy,
            financial_normalizer=financial_normalizer,
            ratios_calculator=ratios_calculator,
            uow_factory=uow_factory,
        )

    def __call__(self, *, start: int = 1, max_nsd: int = 1) -> None:
        try:
            return self.run(start=start, max_nsd=max_nsd)
        except Exception as e:
            pass

    # def sync_nsd(self, *, start: int = 1, max_nsd: Optional[int] = None) -> None:
    #     stream = self.sync_nsd_usecase.stream_nsd(start=start, max_nsd=max_nsd)

    #     # o pool cria WorkerTaskDTO internamente com worker_id próprio
    #     tasks = []
    #     for i, nsd in enumerate(stream):
    #         tasks.append((i, nsd))
    #     # tasks = [(i, nsd) for i, nsd in enumerate(stream)]
    #     if not tasks:
    #         return

    #     self.worker_pool.run(
    #         tasks=tasks,
    #         processor=self._processor,
    #         logger=self.logger,
    #     )
    def run(self, *, start: int = 1, max_nsd: int = 1) -> None:
        # codes = self.sync_nsd_usecase.build_code_list(start=start, max_nsd=max_nsd)
        # from infrastructure.utils import file
        # file.save_list_to_csv(codes, "code_list.csv")

        from infrastructure.utils import file
        codes = file.read_list_from_csv("code_list.csv")
        code_stream = self.sync_nsd_usecase.stream_codes(codes)

        self.worker_pool(
            logger=self.logger,
            tasks=enumerate(code_stream),
            processor=self._processor,
            total_size=len(codes)
        )
