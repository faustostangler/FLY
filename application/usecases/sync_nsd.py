# application/usecases/sync_nsd.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterator, Optional, Protocol, runtime_checkable, Iterable, List

from domain.dtos.nsd_dto import NsdDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from application.ports.uow_port import UowFactoryPort, Uow

@runtime_checkable
class _ScraperProbe(Protocol):
    def find_last_existing_nsd(self, start: int = 1, max_limit: int = 10**10) -> int: ...

class SyncNSDUseCase:
    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        nsd_repository: RepositoryNsdPort,
        company_repository: RepositoryCompanyDataPort,
        scraper: ScraperNsdPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.nsd_repository = nsd_repository
        self.company_repository = company_repository
        self.scraper = scraper
        self.uow_factory = uow_factory

    def stream_nsd(self, *, start: int = 1, max_nsd: Optional[int] = None) -> Iterator[NsdDTO]:
        with self.uow_factory() as uow:
            skip_codes = [int(code) for (code,) in self.nsd_repository.iter_existing_by_columns("nsd", uow=uow)]
            skip_codes = {int(code) for code in (skip_codes or [])}

            max_nsd_probable = max(start, self._find_next_probable_nsd(uow=uow, start=start, safety_factor=1.10))

        # leitura apenas; sem commit explícito
        for dto in self.scraper.iter_nsd(start=start, skip_codes=skip_codes, max_nsd=max_nsd_probable):
            yield dto

    def stream_codes(self, *, start: int = 1, max_nsd: Optional[int] = None) -> Iterator[int]:
        with self.uow_factory() as uow:
            skip_codes = [int(code) for (code,) in self.nsd_repository.iter_existing_by_columns("nsd", uow=uow)]
            start = max(skip_codes) + 1
            max_nsd_probable = self._find_next_probable_nsd(start=start, skip_codes=skip_codes, uow=uow)

        # probe opcional no scraper; se não existir, usa 0
        probe = getattr(self.scraper, "_find_last_existing_nsd", None)
        max_nsd_existing: int = 1
        if callable(probe):
            try:
                max_nsd_existing = int(probe(start=start, max_limit=10**10))
            except Exception as e:
                self.logger.log(f"find_last_existing_nsd failed: {e}", level="warning")

        cap = max_nsd if max_nsd is not None else 0
        max_nsd_final = max(start, max_nsd_existing, max_nsd_probable, cap)
        for code in range(start, max_nsd_final + 1):
            if code in skip_codes:
                continue
            yield code

    def _find_next_probable_nsd(
        self,
        *,
        skip_codes: list[int],
        uow,
        start: int,
        safety_factor: float = 1.10,
    ) -> int:
        if not skip_codes:
            return start

        # lê datas válidas do banco
        dates = [d for (d,) in self.nsd_repository.iter_existing_by_columns("sent_date", uow=uow, include_nulls=False)]

        if not dates:
            return max(start, max(skip_codes))

        first_date = min(dates)
        last_date = max(dates)

        # Days span between dates
        total_span_days = (last_date - first_date).days or 1  # type: ignore[assignment]

        # Daily nsd per day Average
        daily_avg = len(skip_codes) / total_span_days

        # days elapsed since last_date
        days_elapsed = max((datetime.now() - last_date).days, 0)  # type: ignore[assignment]

        # Estimated nsd
        max_nsd_probable = (
            start
            + int(daily_avg * days_elapsed * safety_factor)
            + self.config.scraping.linear_holes
        )

        return max_nsd_probable


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
