from __future__ import annotations

from application.usecases.sync_nsd import SyncNSDUseCase
from domain.ports import (
    RepositoryCompanyDataPort,
    ConfigPort,
    LoggerPort,
    RepositoryNsdPort,
    ScraperNsdPort,
)


class NsdService:
    """Application service that orchestrates NSD synchronization."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: RepositoryNsdPort,
        company_repo: RepositoryCompanyDataPort,
        scraper: ScraperNsdPort,
    ) -> None:
        """Instantiate the service with its required dependencies."""
        self.logger = logger

        # Set up the underlying use case that performs the synchronization.
        self.sync_nsd_usecase = SyncNSDUseCase(
            config=config,
            logger=logger,
            repository=repository,
            company_repo=company_repo,
            scraper=scraper,
        )

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def sync_nsd(self) -> None:
        """Start the NSD synchronization workflow."""
        # Delegate the work to the injected use case.
        # self.logger.log("Call Method controller.start()._nsd_service().sync_nsd().sync_nsd_usecase.synchronize_nsd()", level="info")
        self.sync_nsd_usecase.synchronize_nsd()
        # self.logger.log("End  Method controller.start()._nsd_service().sync_nsd().sync_nsd_usecase.synchronize_nsd()", level="info")
