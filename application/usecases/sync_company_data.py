"""Use case for synchronizing company data between scraper and repository."""

from typing import List

from domain.dtos import CompanyDataDTO
from domain.ports.repository_company_data_port import CompanyDataRepositoryPort
from domain.ports.scraper_company_data_port import CompanyDataScraperPort
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort

# from infrastructure.helpers.list_flattener import ListFlattener


class SyncCompanyDataUseCase:
    """Synchronize company data from the scraper to the repository."""

    def __init__(
        self,
        config: ConfigPort, 
        logger: LoggerPort,
        repository: CompanyDataRepositoryPort,
        scraper: CompanyDataScraperPort,
        max_workers: int = 1,
    ):
        """Store dependencies and configure use case execution."""
        self.config = config
        self.logger = logger
        self.repository = repository
        self.scraper = scraper
        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def synchronize_companies(self) -> CompanyDataDTO:
        """Start the full synchronization pipeline.

        Steps:
            1. Fetch data from the scraper.
            2. Convert results into ``CompanyDataDTO`` objects.
            3. Persist them using the repository.
        """
        # self.logger.log("Run  Method sync_companies_usecase.run()", level="info")

        # busca todos os company_name que já estão na tabela
        skip_codes = [
            code for (code,) in self.repository.iter_existing_by_columns("company_name")
        ]

        # self.logger.log("Call Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)", level="info")
        # Fetch all companies from the scraper and persist them batch-wise.
        results = self.scraper.fetch_all(
            skip_codes=skip_codes,
            save_callback=self._save_batch,
        )
        # self.logger.log("End  Method sync_companies_usecase.run().fetch_all(save_callback, max_workers)", level="info")

        # Measure download time and network usage.
        bytes_downloaded = self.scraper.metrics_collector.add_network_byte()

        # self.logger.log("End  Method sync_companies_usecase.run()", level="info")

        return SyncCompanyDataResultDTO(
            processed_count=len(results.items),
            skipped_count=len(skip_codes),
            bytes_downloaded=bytes_downloaded,
            elapsed_time=elapsed,
        )

    def _save_batch(self, buffer: List[CompanyDataDTO]) -> None:
        """Convert raw companies to domain DTOs before saving."""
        # primeiro “desembrulha” qualquer nível de listas aninhadas
        flat_items = ListFlattener.flatten(
            buffer
        )  # recebe nested lists, devolve flat list

        # Transform raw DTOs from the scraper to domain DTOs.
        dtos = [CompanyDataDTO.from_raw(item) for item in flat_items]

        # Persist the converted DTOs in bulk for efficiency.
        self.repository.save_all(dtos)

        # self.logger.log("End  Method _save_batch() in SyncCompanyDataUseCase in CompanyDataService", level="info")
