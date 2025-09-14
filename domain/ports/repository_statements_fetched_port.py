from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.statement_fetched_dto import StatementFetchedDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementFetchedPort(RepositoryBasePort[StatementFetchedDTO, int], Protocol):
    """Port definition for persisting fetched financial statements.

    Extends RepositoryBasePort with methods specific to handling fetched
    financial statements associated with companies.
    """

    # def exists_with_hash(self, company_name: str, hash_: str) -> bool:
    #     """Check if a fetched statement already exists for a company and hash.

    #     Args:
    #         company_name (str): Name of the company to check.
    #         hash_ (str): Unique hash identifying the fetched statement.

    #     Returns:
    #         bool: True if a fetched statement with the given hash already exists
    #         for the company, False otherwise.
    #     """
    #     ...

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
