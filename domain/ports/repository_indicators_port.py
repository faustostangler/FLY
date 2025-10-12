from __future__ import annotations

from typing import Protocol, runtime_checkable

# from application.ports.uow_port import Uow
from domain.dtos.indicators_dto import IndicatorsDTO
from domain.ports.repository_base_port import RepositoryBasePort
from application.ports.uow_port import Uow


@runtime_checkable
class RepositoryIndicatorsPort(RepositoryBasePort[IndicatorsDTO, int], Protocol):
    """
    """
