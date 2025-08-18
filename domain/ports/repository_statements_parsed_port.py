from __future__ import annotations

from typing import List

from domain.dtos import ParsedStatementDTO

from .repository_base_port import RepositoryBasePort


class ParsedStatementRepositoryPort(RepositoryBasePort[ParsedStatementDTO, int]):
    """Port for persisting parsed statement rows."""

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Return True when ``company_name`` has ``hash_`` persisted."""

        raise NotImplementedError

    def replace_all_for_company(
        self,
        company_name: str,
        parsed_dtos: List[ParsedStatementDTO],
        new_hash: str,
    ) -> None:
        """Replace all rows for ``company_name`` with ``parsed_dtos``."""

        raise NotImplementedError
