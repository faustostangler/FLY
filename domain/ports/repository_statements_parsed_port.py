from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from domain.dtos import ParsedStatementDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class ParsedStatementRepositoryPort(RepositoryBasePort[ParsedStatementDTO, int], Protocol):
    """Port for persisting parsed statement rows."""

    def exists_with_hash(self, company_name: str, hash_: str) -> bool: ...

    def replace_all_for_company(
        self,
        company_name: str,
        parsed_dtos: List[ParsedStatementDTO],
        new_hash: str,
    ) -> None: ...
