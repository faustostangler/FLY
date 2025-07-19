from __future__ import annotations

from typing import List

from domain.dto import ParsedStatementDTO

from .base_repository_port import SqlAlchemyRepositoryBasePort


class SqlAlchemyParsedStatementRepositoryPort(
    SqlAlchemyRepositoryBasePort[ParsedStatementDTO, int]
):
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
