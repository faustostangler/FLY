from __future__ import annotations

from typing import Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryIndicatorsPort(RepositoryBasePort[IndicatorRecordDTO, int], Protocol):
    """Port interface for persistence operations on CompanyData entities.

    Provides an abstraction for the application layer to interact with
    company-related storage, without depending on a concrete database
    implementation.

    Inherits from:
        RepositoryBasePort[CompanyDataDTO, int]: Base repository contract
        for CRUD operations on CompanyData entities.
    """

    def get_indicator_by_code(self, code: str, *, uow: Uow) -> str | None:
            """Retrieve the indicator for a record by its code.

        Args:
            code (str): The indicator code.

        Returns:
            str: The code associated with the given indicator.
        """
