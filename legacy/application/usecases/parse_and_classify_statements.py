from __future__ import annotations

from domain.dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import ConfigPort, LoggerPort, ParsedStatementRepositoryPort
from infrastructure.helpers import SaveStrategy


class ParseAndClassifyStatementsUseCase:
    """Parse raw HTML and build :class:`ParsedStatementDTO` objects."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: ParsedStatementRepositoryPort,
        config: ConfigPort,
    ) -> None:
        self.logger = logger
        self.repository = repository
        self.strategy: SaveStrategy[ParsedStatementDTO] = SaveStrategy(
            repository.save_all, config=config
        )

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def parse_and_store_row(self, row: RawStatementDTO) -> ParsedStatementDTO:
        """Build a :class:`ParsedStatementDTO` from a statement row."""
        dto = ParsedStatementDTO(
            id=None,
            nsd=row.nsd,
            company_name=row.company_name,
            quarter=row.quarter,
            version=row.version,
            grupo=row.grupo,
            quadro=row.quadro,
            account=row.account,
            description=row.description,
            value=float(row.value),
            processing_hash="",  # ou calcule se necessário
        )
        self.strategy.handle([dto])  # passa como lista para bater com Iterable
        return dto

    def finalize(self) -> None:
        """Flush any buffered statements."""
        self.strategy.finalize()
