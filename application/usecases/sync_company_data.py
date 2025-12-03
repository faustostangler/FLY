from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from infrastructure.utils.list_flatenner import ListFlattener

# from infrastructure.helpers.list_flattener import ListFlattener


class SyncCompanyDataUseCase:
    """Use case for synchronizing company data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        scraper_company_data: ScraperCompanyDataPort,

        uow_factory: UowFactoryPort,

        max_workers: int = 1,
    ):
        """Initialize the use case with its dependencies.

        Args:
            config (ConfigPort): Application configuration provider.
            logger (LoggerPort): Logger interface for capturing messages.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper_company (ScraperCompanyDataPort): Scraper used to fetch company data.
            max_workers (int, optional): Maximum number of workers for parallel execution.
                Defaults to 1, or falls back to the value in the config worker pool.
        """
        self.config = config
        self.logger = logger
        self.repository_company = repository_company
        self.scraper_company_data = scraper_company_data
        self.uow_factory = uow_factory

        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Run the full company synchronization pipeline.

        Steps:
            1. Retrieve company data from the scraper.
            2. Transform results into ``CompanyDataDTO`` objects.
            3. Save them into the repository in batches.

        Returns:
            SyncCompanyDataResultDTO: Summary of the synchronization process,
            including counts and network usage metrics.
        """
        # Collect company identifiers already stored in the repository
        with self.uow_factory() as uow:
            existing_codes = [code for (code,) in self.repository_company.iter_existing_by_columns("company_name", uow=uow)]

            # Fetch companies from scraper and persist them in batch mode
            results = self.scraper_company_data.fetch_all(existing_codes=existing_codes,save_callback=self._save_batch)

            return SyncResultsDTO(items=results, metrics=self.scraper_company_data.get_metrics())

    def _save_batch(
        self,
        items: list[CompanyDataDTO],
        *,
        uow: Uow | None = None,
    ) -> None:
        """Transform and persist a batch of company data.

        Args:
            buffer (List[CompanyDataDTO]): Raw or nested DTOs retrieved by the scraper.
        """
        # type narrowing
        if uow is None:
            raise RuntimeError("SaveCallback chamado sem UoW")

        # with self.uow_factory() as uow:
        # Flatten potential nested lists from scraper output
        flat_items = ListFlattener.flatten(items)

        # Convert raw scraper DTOs into domain-level DTOs
        dtos = [CompanyDataDTO.from_raw(item) for item in flat_items]


        # Persist the transformed DTOs in bulk
        self.repository_company.save_all(dtos, uow=uow)
