from __future__ import annotations

from domain.dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO
from domain.ports import (
    ConfigPort,
    LoggerPort,
    SqlAlchemyParsedStatementRepositoryPort,
)
from domain.utils.statement_processing import classify_section
from infrastructure.helpers import SaveStrategy


class ParseAndClassifyStatementsUseCase:
    """Parse raw HTML and build :class:`ParsedStatementDTO` objects."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: SqlAlchemyParsedStatementRepositoryPort,
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
            batch_id=str(row.nsd),
            account=row.account,
            section=classify_section(row.account),
            value=float(row.value),
            company=row.company_name,
            period=row.quarter,
        )
        self.strategy.handle(dto)
        return dto

    def finalize(self) -> None:
        """Flush any buffered statements."""
        self.strategy.finalize()
