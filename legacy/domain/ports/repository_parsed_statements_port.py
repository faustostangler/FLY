from __future__ import annotations

from typing import List

from domain.dto import StatementFetchedDTO

from .repository_base_port import RepositoryBasePort


class RepositoryStatementFetchedPort(RepositoryBasePort[StatementFetchedDTO, int]):
    """Port for persisting fetched statement rows."""

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Return True when ``company_name`` has ``hash_`` persisted."""

        raise NotImplementedError

    def replace_all_for_company(
        self,
        company_name: str,
        fetched_dtos: List[StatementFetchedDTO],
        new_hash: str,
    ) -> None:
        """Replace all rows for ``company_name`` with ``fetched_dtos``."""

        raise NotImplementedError
