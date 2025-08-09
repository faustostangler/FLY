"""Service layer for company-related synchronization operations."""

from application.ports.config_ports import ConfigPort
from application.usecases.sync_companies import SyncCompanyDataUseCase
from domain.dto import SyncCompanyDataResultDTO
from domain.ports import (
    CompanyDataScraperPort,
    LoggerPort,
    SqlAlchemyCompanyDataRepositoryPort,
)


class CompanyDataService:
    """Coordinate company-related use cases within the application."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: SqlAlchemyCompanyDataRepositoryPort,
        scraper: CompanyDataScraperPort,
    ):
        """Initialize dependencies for company synchronization."""
        self.logger = logger
        self.config = config

        # Create the use case responsible for performing the sync operation.
        self.sync_companies_usecase = SyncCompanyDataUseCase(
            logger=self.logger,
            repository=repository,
            scraper=scraper,
            max_workers=self.config.global_settings.max_workers,
        )

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def sync_companies(self) -> SyncCompanyDataResultDTO:
        """Execute company synchronization using the injected use case."""
        # Delegate execution to the underlying use case and return the result.
        # self.logger.log(
        #     "Call Method sync_companies_usecase.synchronize_companies()",
        #     level="info",
        # )
        result = self.sync_companies_usecase.synchronize_companies()
        # self.logger.log(
        #     "End  Method sync_companies_usecase.synchronize_companies()",
        #     level="info",
        # )
        return result
