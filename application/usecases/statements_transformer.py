from __future__ import annotations

import hashlib

from domain.dtos.parsed_statement_dto import ParsedStatementDTO
from domain.dtos.raw_statement_dto import RawStatementDTO
from domain.ports import DataCleanerPort


class StatementTransformer:
    """Transforms raw financial statements into parsed statements.

    This class uses a data cleaner to sanitize raw statements
    and generates a parsed DTO that includes a content hash
    for uniqueness and traceability.

    Attributes:
        cleaner (DataCleanerPort): Component responsible for cleaning
            and normalizing raw statement data.
    """

    def __init__(self, cleaner: DataCleanerPort) -> None:
        # Data cleaner used for preprocessing statements
        self.cleaner = cleaner

    def transform(self, raw: RawStatementDTO) -> ParsedStatementDTO:
        """Convert a raw statement into a parsed statement.

        Applies data cleaning and computes a unique hash based on
        the normalized content.

        Args:
            raw (RawStatementDTO): Raw financial statement input.

        Returns:
            ParsedStatementDTO: Structured and cleaned statement
            enriched with a deterministic hash.
        """
        pass
