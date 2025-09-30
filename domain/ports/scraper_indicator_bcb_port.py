from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from domain.dtos.indicator_dto import IndicatorRawDTO


class ScraperIndicatorBcbPort(Protocol):
    """External data source contract for Banco Central do Brasil indicators."""

    @abstractmethod
    def fetch(
        self,
        *,
        existing_codes: Iterable[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Iterable[IndicatorRawDTO]:
        """Fetch raw datapoints from BCB for the given codes and interval."""
