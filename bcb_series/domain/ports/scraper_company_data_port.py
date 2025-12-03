from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos.company_data_dto import CompanyDataDTO
from domain.ports.scraper_base_port import ScraperBasePort


@runtime_checkable
class ScraperCompanyDataPort(ScraperBasePort[CompanyDataDTO], Protocol):
    """Abstraction for external company data scrapers returning ``CompanyDataDTO``."""
