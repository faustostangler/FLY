from __future__ import annotations

from typing import Iterable, Protocol, Sequence, runtime_checkable

from application.ports.uow_port import Uow
from datetime import datetime

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

    def get_last_date(self, *, source: str, code: str, uow: Uow) -> datetime | None:
        """Retrieve the most recent persisted date for a given indicator."""

    def get_by_codes(
        self,
        *,
        source: str | None,
        codes: Iterable[str],
    ) -> Sequence[IndicatorRecordDTO]: ...
