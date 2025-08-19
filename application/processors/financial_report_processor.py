# from domain.policies.parsing_policy import ParsingPolicy
from application.usecases.statements_transformer import StatementTransformer
from domain.dtos.raw_statement_dto import RawStatementDTO
from domain.ports.logger_port import LoggerPort
from domain.ports.repository_statements_parsed_port import ParsedStatementRepositoryPort
from domain.ports.repository_statements_raw_port import RawStatementsRepositoryPort
from domain.ports.scraper_raw_statements_port import RawStatementScraperPort
from domain.ports.repository_nsd_port import RepositoryNsdPort


class FinancialReportProcessor:
    def __init__(
        self,
        nsd_repo: RepositoryNsdPort,
        raw_repo: RawStatementsRepositoryPort,
        parsed_repo: ParsedStatementRepositoryPort,
        scraper: RawStatementScraperPort,
        transformer: StatementTransformer,
        logger: LoggerPort,
    ) -> None:
        self.nsd_repo = nsd_repo
        self.raw_repo = raw_repo
        self.parsed_repo = parsed_repo
        self.scraper = scraper
        self.transformer = transformer
        self.logger = logger

    def process(self, nsd_id: int) -> None:
        # 1 nsd sequencial, pega o último válido +1
        # se encontrar nsd, verifica se é do tipo certo
        # build raw_statements links
        # download raw_statements
        # persistencia
        # policy to parse
        # parse if needed
        # load raw compnay year
        # dedupe, sort
        # transform intel
        # transform math
        # persist in parsed
        # persist nsd


        # nsd = self.nsd_repo.get_by_id(nsd_id)
        # if not nsd:
        #     self.logger.log(f"NSD {nsd_id} not found", level="warning")
        #     return

        # # 1. Scraping: sempre salvar RAW
        # raw_doc = self.scraper.fetch(nsd)
        # raw_dto = RawStatementDTO.from_nsd(nsd, raw_doc)
        # self.raw_repo.insert_or_update(raw_dto)

        # # 2. Validação de tipo
        # if not nsd.is_supported_type():
        #     self.logger.log(f"NSD {nsd_id} ignored (unsupported type)", level="info")
        #     return

        # # 3. Política
        # policy = ParsingPolicy.from_nsd(nsd)
        # if not policy.should_parse():
        #     self.logger.log(f"NSD {nsd_id} skipped by policy", level="info")
        #     return

        # # 4. Transformação
        # parsed_dto = self.transformer.transform(raw_dto)

        # # 5. Idempotência
        # current = self.parsed_repo.get_latest_by_key(parsed_dto.key())
        # if current and current.hash == parsed_dto.hash:
        #     self.logger.log(f"NSD {nsd_id} unchanged, no new parsed", level="info")
        #     return

        # # 6. Persistência
        # self.parsed_repo.upsert(parsed_dto)
        # self.logger.log(f"NSD {nsd_id} parsed and saved", level="info")

        return None
