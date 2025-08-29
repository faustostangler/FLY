from __future__ import annotations

import hashlib
from datetime import datetime
from typing import List

from domain.dtos.nsd_dto import NsdDTO
from domain.events.events import NSDReady
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.repositories.outbox_repository import SqlAlchemyOutboxRepository
from infrastructure.utils.clock import UtcClock
from infrastructure.utils.id_generator import IdGenerator
from infrastructure.utils.list_flatenner import ListFlattener


class SyncNSDUseCase:
    """Use case for synchronizing NSD documents and emitting events.

    Contract matches the original legacy version so services can swap
    implementations without changing their calls.
    """

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
        self.id_generator = IdGenerator(config=config)
        self.clock = UtcClock()
        # Local session factory used only for outbox persistence
        self._engine_setup = EngineSetup(
            self.config.database.connection_string, self.logger
        )

    def synchronize_nsd(self) -> None:
        # Collect NSDs already present to skip duplicates
        existing_nsd = [
            code for (code,) in self.nsd_repository.iter_existing_by_columns("nsd")
        ]

        # Fetch and persist NSDs in batches via callback
        self.scraper.fetch_all(
            skip_codes=existing_nsd,
            save_callback=self._save_batch,
        )

    def _save_batch(self, buffer: List[NsdDTO]) -> None:
        # Flatten potential nested lists
        flat_items = ListFlattener.flatten(buffer)
        dtos = [NsdDTO.from_raw(item) for item in flat_items]

        # Ensure company registry contains any missing names
        names = {dto.company_name for dto in dtos if dto.company_name}
        existing_companies = {
            company_name
            for (company_name,) in self.company_repository.iter_existing_by_columns(
                "company_name"
            )
        }
        missing = names - existing_companies
        if missing:
            from domain.dtos.company_data_dto import CompanyDataDTO

            to_create = [
                CompanyDataDTO(
                    cvm_code=self.id_generator.create_id(size=6),
                    company_name=name,
                )
                for name in missing
            ]
            self.company_repository.save_all(to_create)

        # Persist NSDs
        self.nsd_repository.save_all(dtos)

        # Emit NSDReady events into the outbox for downstream processors
        self._publish_nsd_ready_events(dtos)

    def _publish_nsd_ready_events(self, dtos: List[NsdDTO]) -> None:
        if not dtos:
            return
        session = self._engine_setup.Session()
        try:
            outbox = SqlAlchemyOutboxRepository(session)
            now = self.clock.now()
            for dto in dtos:
                # Deterministic version hash from NSD attributes
                basis = f"{dto.nsd}|{dto.version or ''}|{(dto.sent_date or datetime.min).isoformat()}".encode(
                    "utf-8"
                )
                version_hash = hashlib.sha256(basis).hexdigest()
                evt = NSDReady(
                    nsd_id=dto.nsd,  # using NSD code as a stable identifier
                    version_hash=version_hash,
                    occurred_at=now,
                    correlation_id=self.id_generator.create_id(12),
                )
                outbox.add(topic="NSDReady", event_obj=evt, occurred_at=now)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
