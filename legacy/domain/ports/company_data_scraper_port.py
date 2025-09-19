"""Port definitions for external company data sources."""

from __future__ import annotations

from domain.dto.raw_company_data_dto import CompanyDataRawDTO

from .base_scraper_port import BaseScraperPort


class CompanyDataScraperPort(BaseScraperPort[CompanyDataRawDTO]):
    """Port for external company data providers."""
