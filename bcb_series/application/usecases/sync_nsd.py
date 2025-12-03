# application/usecases/sync_nsd.py
from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, Iterator, List, Optional, cast

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.nsd_dto import NsdDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.scraper_nsd_port import ScraperNsdPort


class SyncNSDUseCase:
    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository_nsd: RepositoryNsdPort,
        repository_company: RepositoryCompanyDataPort,
        scraper: ScraperNsdPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.repository_nsd = repository_nsd
        self.repository_company = repository_company
        self.scraper = scraper
        self.uow_factory = uow_factory

    def stream_nsd(self, *, start: int = 1, max_nsd: Optional[int] = None) -> Iterator[NsdDTO]:
        with self.uow_factory() as uow:
            existing_codes = [int(code) for (code,) in self.repository_nsd.iter_existing_by_columns("nsd", uow=uow)]

            max_nsd_probable = max(start, self._find_next_probable_nsd(start=start, existing_codes=existing_codes, safety_factor=1.10, uow=uow))

        # leitura apenas; sem commit explícito
        for dto in self.scraper.iter_nsd(start=start, existing_codes=existing_codes, max_nsd=max_nsd_probable):
            yield dto

    def build_code_list(self, *, start: int = 0, max_nsd: Optional[int] = None) -> List[int]:
        """Lista de NSDs a processar:
        missing = [start..last_nsd] \\ skip_codes
        tail    = [last_nsd+1..end], onde end = max(max_nsd_existing, max_nsd_probable, cap_param)
        """
        start = max(1, int(start))
        cap_param = max_nsd or self.config.repository.batch_size or 50

        with self.uow_factory() as uow:
            existing_codes: list[int] = [int(c) for (c,) in self.repository_nsd.get_all_by_columns("nsd", uow=uow)]
            skip_codes = set(existing_codes)
            last_nsd = max(existing_codes) if existing_codes else 1

            max_nsd_probable: int = self._find_next_probable_nsd(
                start=start,
                existing_codes=existing_codes,
                uow=uow,
            )

        # limites base
        probe_attr = getattr(self.scraper, "_find_last_existing_nsd", None)
        probe: Optional[Callable[..., int]] = (
            cast(Callable[..., int], probe_attr) if callable(probe_attr) else None
        )
        if probe is not None:
            try:
                max_nsd_existing = int(probe(start=max_nsd_probable, max_limit=10**10))
            except Exception:
                max_nsd_existing = 1
        else:
            max_nsd_existing = 1

        end = max(max_nsd_existing, max_nsd_probable, cap_param)

        # missing até last_nsd, mas limitado por end
        missing_nsd = [c for c in range(start, min(last_nsd, end) + 1) if c not in skip_codes]

        # cauda nova a partir do próximo após o último existente
        tail_start = max(last_nsd, start)
        tail = list(range(tail_start, end + 1)) if end >= tail_start else []

        return missing_nsd + tail if len(missing_nsd) > (end - last_nsd) else tail

    def stream_codes(self, codes: Iterable[int]) -> Iterator[int]:
        """Gerador preguiçoso sobre a lista já calculada externamente."""
        for code in codes:
            yield code

    def _find_next_probable_nsd(
        self,
        *,
        existing_codes: list[int],
        uow,
        start: int,
        safety_factor: float = 1.10,
    ) -> int:
        if not existing_codes:
            return start

        # lê datas válidas do banco
        dates = [d for (d,) in self.repository_nsd.iter_existing_by_columns("sent_date", uow=uow, include_nulls=False)]

        if not dates:
            return max(start, max(existing_codes))

        first_date = min(dates)
        last_date = max(dates)

        # Days span between dates
        total_span_days = (last_date - first_date).days or 1  # type: ignore[assignment]

        # Daily nsd per day Average
        daily_avg = len(existing_codes) / total_span_days

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
    #         code for (code,) in self.repository_nsd.iter_existing_by_columns("nsd")
    #     ]

    #     # Fetch all documents from the scraper, persisting them in batches.
    #     # self.logger.log("Call Method controller.run()._nsd_service().run().sync_nsd_usecase.run().fetch_all()", level="info")
    #     self.scraper.fetch_all(
    #         existing_codes=existing_nsd,
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
    #         for (company_name,) in self.repository_company.iter_existing_by_columns(
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
    #         self.repository_company.save_all(to_create)

    #     # Save the batch to the repository in a single call.
    #     self.repository_nsd.save_all(dtos)
