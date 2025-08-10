"""Port for transforming raw statement rows into parsed ones."""

from __future__ import annotations

from typing import List, Protocol

from domain.dto.parsed_statement_dto import ParsedStatementDTO
from domain.dto.raw_statement_dto import RawStatementDTO


class StatementTransformerPort(Protocol):
    """Interface for statement transformation adapters."""

    def transform(self, rows: List[RawStatementDTO]) -> List[ParsedStatementDTO]:
        """Transform ``rows`` into cleaned ``ParsedStatementDTO`` objects."""
        raise NotImplementedError
