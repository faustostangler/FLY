from __future__ import annotations

from typing import List

from domain.dto import StatementRawDTO

from .repository_base_port import RepositoryBasePort


class RepositoryStatementRawPort(RepositoryBasePort[StatementRawDTO, int]):
    """Port for persisting raw statement rows."""

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Return True when ``company_name`` has ``hash_`` persisted."""

        raise NotImplementedError

    def replace_all_for_company(
        self,
        company_name: str,
        raw_dtos: List[StatementRawDTO],
        new_hash: str,
    ) -> None:
        """Replace all rows for ``company_name`` with ``raw_dtos``."""


    def get_by_company_name(self, company_name: str) -> List[StatementRawDTO]:
        """Return all raw rows for ``company_name``."""

        raise NotImplementedError


