from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from domain.dtos import StatementParsedDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementParsedPort(RepositoryBasePort[StatementParsedDTO, int], Protocol):
    """Port definition for persisting parsed financial statements.

    Extends RepositoryBasePort with methods specific to handling parsed
    financial statements associated with companies.
    """

    def exists_with_hash(self, company_name: str, hash_: str) -> bool:
        """Check if a parsed statement already exists for a company and hash.

        Args:
            company_name (str): Name of the company to check.
            hash_ (str): Unique hash identifying the parsed statement.

        Returns:
            bool: True if a parsed statement with the given hash already exists
            for the company, False otherwise.
        """
        ...

    def replace_all_for_company(
        self,
        company_name: str,
        parsed_dtos: List[StatementParsedDTO],
        new_hash: str,
    ) -> None:
        """Replace all parsed statements for a company with a new set.

        Args:
            company_name (str): Name of the company whose statements are updated.
            parsed_dtos (List[StatementParsedDTO]): New list of parsed statements
                to persist in place of the old ones.
            new_hash (str): Hash associated with the new parsed statements.

        Returns:
            None
        """
        ...
