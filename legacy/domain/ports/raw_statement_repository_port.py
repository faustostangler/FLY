from __future__ import annotations

from abc import ABC
from typing import List

from domain.dtos.raw_statement_dto import RawStatementDTO

from .base_repository_port import RepositoryBasePort


class RawStatementRepositoryPort(RepositoryBasePort[RawStatementDTO, int], ABC):
    """Port for persisting raw statement rows."""

    def get_by_company_name(self, company_name: str) -> List[RawStatementDTO]:
        """Return all raw rows for ``company_name``."""

        raise NotImplementedError
