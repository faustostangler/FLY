from domain.ports import (
    CompanyDataRepositoryPort,
    CompanyDataScraperPort,
    ConfigPort,
    LoggerPort,
)
from domain.services import CompanyDataService


class Cli():
    def __init__(self, config: ConfigPort, logger: LoggerPort, company_repository: CompanyDataRepositoryPort, company_scraper: CompanyDataScraperPort) -> None:
        self.config = config
        self.logger = logger
        self.company_repository = company_repository
        self.company_scraper = company_scraper

    def run(self) -> None:
        self.logger.log("Start FLY", level="info")
        # Aqui você chama os processors, controllers, etc.
        self._company_service()

    def _company_service(self) -> None:
        """Build and execute the company data synchronization flow."""
        company_repository = self.company_repository
        company_scraper = self.company_scraper

        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repository,
            scraper=company_scraper,
        )
        company_service.sync_companies()

