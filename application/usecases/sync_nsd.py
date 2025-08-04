from __future__ import annotations

from domain.dto.nsd_dto import NsdDTO
from domain.ports import LoggerPort, NSDRepositoryPort, NSDSourcePort
from infrastructure.helpers.list_flattener import ListFlattener
from typing import Set, Union


class SyncNSDUseCase:
    """Use case responsible for synchronizing NSD documents."""

    def __init__(
        self,
        logger: LoggerPort,
        repository: NSDRepositoryPort,
        scraper: NSDSourcePort,
    ) -> None:
        """Store dependencies required for synchronization."""
        self.logger = logger
        self.repository = repository
        self.scraper = scraper

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def synchronize_nsd(self) -> None:
        """Start the NSD synchronization workflow."""

        # self.logger.log("Run  Method controller.run()._nsd_service().run().sync_nsd_usecase.run()", level="info")

        # Retrieve any previously stored document IDs to avoid duplicates.
        existing_ids = self.repository.get_all_primary_keys()

        # busca todos os cvm_code que já estão na tabela
        raw = self.repository.get_existing_by_columns("nsd")
        # get_existing_by_columns devolve List[Tuple], ex: [("900049",),("900642",)…]
        existing_ids = [code for (code,) in raw]


        # Fetch all documents from the scraper, persisting them in batches.
        # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")
        self.scraper.fetch_all(
            skip_codes=existing_ids,
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

        flat_items = ListFlattener.flatten(buffer)  # recebe nested lists, devolve flat list

        # Transform raw DTOs from the scraper to domain DTOs.
        dtos = [NsdDTO.from_raw(item) for item in flat_items]

        # Save the batch to the repository in a single call.
        self.repository.save_all(dtos)
