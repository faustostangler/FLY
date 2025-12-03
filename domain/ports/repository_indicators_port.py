from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.indicators_dto import IndicatorsDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryIndicatorsPort(RepositoryBasePort[IndicatorsDTO, int], Protocol):
    """Port definition for repositories handling indicator data."""
