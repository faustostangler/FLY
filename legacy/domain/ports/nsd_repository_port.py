"""Port definitions for NSD persistence repositories."""

from __future__ import annotations

from abc import abstractmethod
from typing import List, Set

from domain.dtos.nsd_dto import NsdDTO

from .base_repository_port import RepositoryBasePort


class NSDRepositoryPort(RepositoryBasePort[NsdDTO, int]):
    """Port for NSD persistence operations."""

    @abstractmethod
    def get_all_pending(
        self,
        company_names: Set[str],
        valid_types: Set[str],
        exclude_nsd: Set[str],
    ) -> List[NsdDTO]:
        """Retorna todos os NSDs válidos ainda não processados."""
        raise NotImplementedError
