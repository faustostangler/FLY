from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.ratio_result_dto import RatioResultDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryRatiosPort(RepositoryBasePort[RatioResultDTO, int], Protocol):
    """Persistence port for computed ratio metrics."""

