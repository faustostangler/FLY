from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.statement_fetched_dto import StatementFetchedDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementFetchedPort(RepositoryBasePort[StatementFetchedDTO, int], Protocol):
    """Port definition for persisting fetched financial statements.

    Extends RepositoryBasePort with methods specific to handling fetched
    financial statements associated with companies.
    """

    def exists_with_hash(
        self,
        *,
        company_name: Optional[str],
        hash_: str,
        uow: Uow,
    ) -> bool:
        """Return True when ``company_name`` has ``hash_`` persisted."""
        ...

    # def replace_all_for_company(
    #     self,
    #     company_name: str,
    #     fetched_dtos: List[StatementFetchedDTO],
    #     new_hash: str,
    # ) -> None:
    #     """Replace all fetched statements for a company with a new set.

    #     Args:
    #         company_name (str): Name of the company whose statements are updated.
    #         fetched_dtos (List[StatementFetchedDTO]): New list of fetched statements
    #             to persist in place of the old ones.
    #         new_hash (str): Hash associated with the new fetched statements.

    #     Returns:
    #         None
    #     """
    #     ...
