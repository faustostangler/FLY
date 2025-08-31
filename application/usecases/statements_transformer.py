from __future__ import annotations

import hashlib

from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.ports.datacleaner_port import DataCleanerPort


class StatementTransformer:
    """Transforms raw financial statements into fetched statements.

    This class uses a data cleaner to sanitize raw statements
    and generates a fetched DTO that includes a content hash
    for uniqueness and traceability.

    Attributes:
        cleaner (DataCleanerPort): Component responsible for cleaning
            and normalizing raw statement data.
    """

    def __init__(self, cleaner: DataCleanerPort) -> None:
        # Data cleaner used for preprocessing statements
        self.cleaner = cleaner

    def transform(self, raw: StatementRawDTO) -> StatementFetchedDTO:
        """Convert a raw statement into a fetched statement.

        Applies data cleaning and computes a unique hash based on
        the normalized content.

        Args:
            raw (StatementRawDTO): Raw financial statement input.

        Returns:
            StatementFetchedDTO: Structured and cleaned statement
            enriched with a deterministic hash.
        """
        pass
