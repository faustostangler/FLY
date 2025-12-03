from application.ports.logger_port import LoggerPort
from application.usecases.statements_transformer import StatementTransformer
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort


class FinancialReportProcessor:
    """Orquestra o processamento ponta-a-ponta de um NSD.

    Fluxo previsto:
      1) Carrega e valida o NSD.
      2) Busca e persiste sempre os RAW (trilha de auditoria).
      3) Avalia política de parsing.
      4) Transforma RAW -> FETCHED.
      5) Upsert dos FETCHED e atualização de estado do NSD.

    A implementação concreta depende das portas injetadas.
    """

    def __init__(
        self,
        nsd_repo: RepositoryNsdPort,
        raw_repo: RepositoryStatementsRawPort,
        fetched_repo: RepositoryStatementFetchedPort,
        scraper: ScraperStatementRawPort,
        transformer: StatementTransformer,
        logger: LoggerPort,
    ) -> None:
        # Colaboradores necessários
        self.nsd_repo = nsd_repo
        self.raw_repo = raw_repo
        self.fetched_repo = fetched_repo
        self.scraper = scraper
        self.transformer = transformer
        self.logger = logger

    def process(self, nsd_id: int) -> None:
        """Processa um NSD ponta-a-ponta.

        Mantido como esqueleto com passos comentados para não alterar o runtime atual.
        """
        # nsd = self.nsd_repo.get_by_id(nsd_id)
        # if not nsd:
        #     self.logger.log(f"NSD {nsd_id} not found", level="warning")
        #     return
        #
        # raw_doc = self.scraper.fetch(nsd)
        # raw_dto = StatementRawDTO.from_nsd(nsd, raw_doc)
        # self.raw_repo.insert_or_update(raw_dto)
        #
        # if not nsd.is_supported_type():
        #     self.logger.log(f"NSD {nsd_id} ignored (unsupported type)", level="info")
        #     return
        #
        # fetched = self.transformer.transform(raw_dto)
        #
        # if self.fetched_repo.is_duplicate(fetched):
        #     self.logger.log("Duplicate fetched content. Skipping persist.", level="info")
        #     return
        #
        # self.fetched_repo.insert_or_update(fetched)
        # self.nsd_repo.mark_processed(nsd_id)
        # self.logger.log(f"NSD {nsd_id} processed successfully.", level="info")
