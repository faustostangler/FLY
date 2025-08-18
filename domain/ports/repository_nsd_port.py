from __future__ import annotations

from typing import List, Protocol, Set, runtime_checkable

from domain.dtos import NsdDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryNsdPort(RepositoryBasePort[NsdDTO, int], Protocol):
    """Port for NSD persistence operations."""

    def get_all_pending(
        self,
        company_names: Set[str],
        valid_types: Set[str],
        exclude_nsd: Set[str],
    ) -> List[NsdDTO]: ...
