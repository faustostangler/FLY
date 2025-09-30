from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from domain.dtos.indicator_dto import IndicatorRawDTO
from domain.ports.scraper_indicator_bcb_port import ScraperIndicatorBcbPort


class IndicatorBcbScraper(ScraperIndicatorBcbPort):
    """Concrete scraper for Banco Central do Brasil indicator data."""

    def fetch(
        self,
        *,
        existing_codes: Iterable[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Iterable[IndicatorRawDTO]:
        raise NotImplementedError
