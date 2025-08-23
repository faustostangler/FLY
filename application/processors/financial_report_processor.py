from application.usecases.statements_transformer import StatementTransformer
from domain.dtos.raw_statement_dto import RawStatementDTO
from domain.ports.logger_port import LoggerPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_parsed_port import ParsedStatementRepositoryPort
from domain.ports.repository_statements_raw_port import RawStatementsRepositoryPort
from domain.ports.scraper_raw_statements_port import RawStatementScraperPort


class FinancialReportProcessor:
    """Orchestrates the end‑to‑end processing of a financial report (NSD).

    This service coordinates fetching raw statements, validating NSD eligibility,
    applying parsing policies, transforming content, enforcing idempotency, and
    persisting both raw and parsed artifacts.

    The concrete behavior depends on the provided ports (repositories/scraper),
    transformer, and logger, enabling easy substitution in tests or different
    runtime environments.
    """

    def __init__(
        self,
        nsd_repo: RepositoryNsdPort,
        raw_repo: RawStatementsRepositoryPort,
        parsed_repo: ParsedStatementRepositoryPort,
        scraper: RawStatementScraperPort,
        transformer: StatementTransformer,
        logger: LoggerPort,
    ) -> None:
        """Initialize the processor with infrastructure ports and helpers.

            nsd_repo: Repository to read and persist NSD metadata/state.
            raw_repo: Repository responsible for raw statements persistence.
            parsed_repo: Repository responsible for parsed statements persistence.
            scraper: Adapter that fetches raw statements/documents for a given NSD.
            transformer: Pure transformation logic from raw DTO to parsed DTO.
            logger: Structured logger for operational messages.

        Raises:
            ValueError: If any required dependency is missing (not validated here,
                but callers should pass valid implementations).
        """
        # Keep references to all required collaborators
        self.nsd_repo = nsd_repo
        self.raw_repo = raw_repo
        self.parsed_repo = parsed_repo
        self.scraper = scraper
        self.transformer = transformer
        self.logger = logger

    def process(self, nsd_id: int) -> None:
        """Process a single NSD end‑to‑end.

        High‑level flow:
            1) Load NSD and validate existence/type.
            2) Always fetch and persist RAW statements (audit trail).
            3) Evaluate parsing policy to decide whether to parse now.
            4) Transform RAW -> PARSED.
            5) Enforce idempotency via content hash comparison.
            6) Upsert parsed output and update NSD state.

        Args:
            nsd_id: Unique identifier of the NSD to process.

        Returns:
            None
        """
        # Outline the intended orchestration for future implementation
        # (kept commented to preserve current behavior while documenting intent)
        #
        # Retrieve the NSD by id; if not found, log and exit early
        # nsd = self.nsd_repo.get_by_id(nsd_id)
        # if not nsd:
        #     self.logger.log(f"NSD {nsd_id} not found", level="warning")
        #     return
        #
        # Always scrape and persist the raw document to maintain an audit trail
        # raw_doc = self.scraper.fetch(nsd)
        # raw_dto = RawStatementDTO.from_nsd(nsd, raw_doc)
        # self.raw_repo.insert_or_update(raw_dto)
        #
        # Validate whether this NSD type is supported before parsing
        # if not nsd.is_supported_type():
        #     self.logger.log(f"NSD {nsd_id} ignored (unsupported type)", level="info")
        #     return
        #
        # Determine parsing policy for this NSD and honor skip decisions
        # policy = ParsingPolicy.from_nsd(nsd)
        # if not policy.should_parse():
        #     self.logger.log(f"NSD {nsd_id} skipped by policy", level="info")
        #     return
        #
        # Transform raw statements into the normalized parsed representation
        # parsed_dto = self.transformer.transform(raw_dto)
        #
        # Ensure idempotency: skip if nothing changed (hash comparison)
        # current = self.parsed_repo.get_latest_by_key(parsed_dto.key())
        # if current and current.hash == parsed_dto.hash:
        #     self.logger.log(f"NSD {nsd_id} unchanged, no new parsed", level="info")
        #     return
        #
        # Persist parsed output and record success
        # self.parsed_repo.upsert(parsed_dto)
        # self.logger.log(f"NSD {nsd_id} parsed and saved", level="info")

        # Explicitly return None for clarity of intent
        return None
