"""Port definitions for external company data sources."""

from __future__ import annotations

from domain.dto.raw_company_data_dto import CompanyDataRawDTO

from .scraper_base_port import ScraperBasePort


class ScraperCompanyDataPort(ScraperBasePort[CompanyDataRawDTO]):
    """Port for external company data providers."""
