from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.ports.scraper_base_port import ScraperBasePort


@runtime_checkable
class ScraperIndicatorsPort(ScraperBasePort[IndicatorRecordDTO], Protocol):
    """Abstraction for external data scrapers returning ``DTO``."""
