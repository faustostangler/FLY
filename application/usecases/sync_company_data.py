from typing import List

from domain.dtos import CompanyDataDTO
from domain.ports.repository_company_data_port import CompanyDataRepositoryPort
from domain.ports.scraper_company_data_port import CompanyDataScraperPort
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort

# from infrastructure.helpers.list_flattener import ListFlattener


class SyncCompanyDataUseCase:
    """Use case for synchronizing company data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort, 
        logger: LoggerPort,
        repository: CompanyDataRepositoryPort,
        scraper: CompanyDataScraperPort,
        max_workers: int = 1,
    ):
        """Initialize the use case with its dependencies.

        Args:
            config (ConfigPort): Application configuration provider.
            logger (LoggerPort): Logger interface for capturing messages.
            repository (CompanyDataRepositoryPort): Repository for persisting company data.
            scraper (CompanyDataScraperPort): Scraper used to fetch company data.
            max_workers (int, optional): Maximum number of workers for parallel execution.
                Defaults to 1, or falls back to the value in the config worker pool.
        """
        self.config = config
        self.logger = logger
        self.repository = repository
        self.scraper = scraper
        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def synchronize_companies(self) -> CompanyDataDTO:
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
        skip_codes = [
            code for (code,) in self.repository.iter_existing_by_columns("company_name")
        ]

        # Fetch companies from scraper and persist them in batch mode
        results = self.scraper.fetch_all(
            skip_codes=skip_codes,
            save_callback=self._save_batch,
        )

        # Collect metrics from the scraper (downloaded bytes, timings, etc.)
        bytes_downloaded = self.scraper.metrics_collector.add_network_byte()

        return SyncCompanyDataResultDTO(
            processed_count=len(results.items),
            skipped_count=len(skip_codes),
            bytes_downloaded=bytes_downloaded,
            elapsed_time=elapsed,
        )

    def _save_batch(self, buffer: List[CompanyDataDTO]) -> None:
        """Transform and persist a batch of company data.

        Args:
            buffer (List[CompanyDataDTO]): Raw or nested DTOs retrieved by the scraper.
        """
        # Flatten potential nested lists from scraper output
        flat_items = ListFlattener.flatten(buffer)

        # Convert raw scraper DTOs into domain-level DTOs
        dtos = [CompanyDataDTO.from_raw(item) for item in flat_items]

        # Persist the transformed DTOs in bulk
        self.repository.save_all(dtos)
