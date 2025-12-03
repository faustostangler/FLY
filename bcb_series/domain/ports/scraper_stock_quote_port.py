from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.scraper_base_port import ScraperBasePort


@runtime_checkable
class ScraperStockQuotePort(ScraperBasePort[StockQuoteDTO], Protocol):
    """Abstraction for external data scrapers returning ``DTO``."""
