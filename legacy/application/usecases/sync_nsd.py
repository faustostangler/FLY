from __future__ import annotations

from domain.dto.nsd_dto import NsdDTO
from domain.ports import (
    RepositoryCompanyDataPort,
    ConfigPort,
    LoggerPort,
    RepositoryNsdPort,
    ScraperNsdPort,
)
from infrastructure.helpers.list_flattener import ListFlattener
from infrastructure.utils.id_generator import IdGenerator


class SyncNSDUseCase:
    """Use case responsible for synchronizing NSD documents."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: RepositoryNsdPort,
        company_repo: RepositoryCompanyDataPort,
        scraper: ScraperNsdPort,
    ) -> None:
        """Store dependencies required for synchronization."""
        self.config = config
        self.logger = logger
        self.repository = repository
        self.company_repo = company_repo
        self.scraper = scraper
        self.id_generator = IdGenerator(config=config)

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def synchronize_nsd(self) -> None:
        """Start the NSD synchronization workflow."""

        # self.logger.log("Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run()", level="info")

        # busca todos os cvm_code que já estão na tabela
        existing_nsd = [
            code for (code,) in self.repository.iter_existing_by_columns("nsd")
        ]

        # Fetch all documents from the scraper, persisting them in batches.
        # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")
        self.scraper.fetch_all(
            existing_codes=existing_nsd,
            save_callback=self._save_batch,
        )
        # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")

        # Record metrics about the synchronization process.
        # self.logger.log(
        #     f"Downloaded {self.scraper.metrics_collector.network_bytes} bytes",
        #     level="info",
        # )

        # self.logger.log("End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run()", level="info")

    def _save_batch(self, buffer: list[NsdDTO]) -> None:
        """Persist a batch of raw data after converting to domain DTOs."""

        flat_items = ListFlattener.flatten(
            buffer
        )  # recebe nested lists, devolve flat list

        # Transform raw DTOs from the scraper to domain DTOs.
        dtos = [NsdDTO.from_raw(item) for item in flat_items]

        names = {dto.company_name for dto in dtos if dto.company_name}
        # → busca os já cadastrados
        existing_companies = {
            company_name
            for (company_name,) in self.company_repo.iter_existing_by_columns(
                "company_name"
            )
        }
        missing = names - existing_companies
        if missing:
            from domain.dto.company_data_dto import CompanyDataDTO

            to_create = [
                CompanyDataDTO(
                    cvm_code=self.id_generator.create_id(size=6), company_name=name
                )
                for name in missing
            ]
            # insere todas as empresas faltantes de uma vez
            self.company_repo.save_all(to_create)

        # Save the batch to the repository in a single call.
        self.repository.save_all(dtos)
