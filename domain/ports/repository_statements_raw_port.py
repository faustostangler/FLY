from __future__ import annotations

from abc import ABC
from typing import List

from domain.dtos import RawStatementDTO

from .repository_base_port import RepositoryBasePort


class RawStatementsRepositoryPort(RepositoryBasePort[RawStatementDTO, int], ABC):
    """Port for persisting raw statement rows."""

    def get_by_company_name(self, company_name: str) -> List[RawStatementDTO]:
        """Return all raw rows for ``company_name``."""

        raise NotImplementedError
