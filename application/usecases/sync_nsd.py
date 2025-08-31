# application/usecases/sync_nsd.py
from __future__ import annotations
from typing import Iterator, Optional
from domain.dtos.nsd_dto import NsdDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_nsd_port import ScraperNsdPort

class SyncNSDUseCase:
    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        nsd_repository: RepositoryNsdPort,
        company_repository: RepositoryCompanyDataPort,
        scraper: ScraperNsdPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.nsd_repository = nsd_repository
        self.company_repository = company_repository
        self.scraper = scraper

    def stream_nsd(self, *, start: int = 1, max_nsd: Optional[int] = None) -> Iterator[NsdDTO]:
        existing = [code for (code,) in self.nsd_repository.iter_existing_by_columns("nsd")]
        for dto in self.scraper.iter_nsd(start=start, skip_codes=existing, max_nsd=max_nsd):
            yield dto

    # def synchronize_nsd(self) -> None:
    #     """Start the NSD synchronization workflow."""

    #     # self.logger.log("Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run()", level="info")

    #     # busca todos os cvm_code que já estão na tabela
    #     existing_nsd = [
    #         code for (code,) in self.nsd_repository.iter_existing_by_columns("nsd")
    #     ]

    #     # Fetch all documents from the scraper, persisting them in batches.
    #     # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")
    #     self.scraper.fetch_all(
    #         skip_codes=existing_nsd,
    #         save_callback=self._save_batch,
    #     )
    #     # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")

    #     # Record metrics about the synchronization process.
    #     # self.logger.log(
    #     #     f"Downloaded {self.scraper.metrics_collector.network_bytes} bytes",
    #     #     level="info",
    #     # )

    #     # self.logger.log("End  Method controller.run()._nsd_service().run().sync_nsd_usecase.run()", level="info")

    # def _save_batch(self, buffer: list[NsdDTO]) -> None:
    #     """Persist a batch of raw data after converting to domain DTOs."""

    #     flat_items = ListFlattener.flatten(
    #         buffer
    #     )  # recebe nested lists, devolve flat list

    #     # Transform raw DTOs from the scraper to domain DTOs.
    #     dtos = [NsdDTO.from_raw(item) for item in flat_items]

    #     names = {dto.company_name for dto in dtos if dto.company_name}
    #     # → busca os já cadastrados
    #     existing_companies = {
    #         company_name
    #         for (company_name,) in self.company_repository.iter_existing_by_columns(
    #             "company_name"
    #         )
    #     }
    #     missing = names - existing_companies
    #     if missing:
    #         from domain.dtos.company_data_dto import CompanyDataDTO

    #         to_create = [
    #             CompanyDataDTO(
    #                 cvm_code=self.id_generator.create_id(size=6), company_name=name
    #             )
    #             for name in missing
    #         ]
    #         # insere todas as empresas faltantes de uma vez
    #         self.company_repository.save_all(to_create)

    #     # Save the batch to the repository in a single call.
    #     self.nsd_repository.save_all(dtos)
