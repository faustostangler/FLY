from __future__ import annotations

from typing import List, Protocol, Set, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos import NsdDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryNsdPort(RepositoryBasePort[NsdDTO, int], Protocol):
    """Persistence port for NSD entities.

    Defines the contract for interacting with NSD storage,
    following the hexagonal architecture pattern.

    Inherits:
        RepositoryBasePort[NsdDTO, int]: Base repository port
        parametrized for `NsdDTO` entities with `int` as the identifier type.
    """

    def get_all_pending(
        self,
        company_names: Set[str],
        valid_types: Set[str],
        exclude_nsd: Set[str],
        *,
        uow: Uow,
    ) -> List[NsdDTO]:
        """Retrieve all pending NSD entries matching the given criteria.

        Args:
            company_names (Set[str]): Filter by companies of interest.
            valid_types (Set[str]): Restrict results to specific NSD types.
            exclude_nsd (Set[str]): NSD identifiers to exclude from results.

        Returns:
            List[NsdDTO]: A list of pending NSD objects that match the filters.
        """
        ...
