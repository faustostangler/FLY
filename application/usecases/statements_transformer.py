from __future__ import annotations

import hashlib

from domain.dtos import ParsedStatementDTO, RawStatementDTO
from domain.ports import DataCleanerPort


class StatementTransformer:
    """Transforma RawStatementDTO em ParsedStatementDTO com limpeza e hash."""

    def __init__(self, cleaner: DataCleanerPort) -> None:
        self.cleaner = cleaner

    def transform(self, raw: RawStatementDTO) -> None:  # -> ParsedStatementDTO:
        pass
