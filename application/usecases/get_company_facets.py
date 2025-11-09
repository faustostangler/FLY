from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort


@dataclass(frozen=True)
class CompanyFacetsResult:
    facets: Dict[str, List[str]]


class GetCompanyFacetsUseCase:
    def __init__(
        self,
        *,
        repository: CompaniesEligiblePort,
        uow_factory: UowFactoryPort,
        logger: LoggerPort | None = None,
    ) -> None:
        self._repository = repository
        self._uow_factory = uow_factory
        self._logger = logger

    def __call__(self) -> CompanyFacetsResult:
        return self.run()

    def run(self) -> CompanyFacetsResult:
        with self._uow_factory() as uow:
            dtos: list[CompanyEligibleDTO] = list(
                self._repository.iter_all(uow=uow, batch_size=1000)
            )

        sectors: set[str] = set()
        subsectors: set[str] = set()
        segments: set[str] = set()
        markets: set[str] = set()

        for dto in dtos:
            if dto.industry_sector:
                sectors.add(dto.industry_sector)
            if dto.industry_subsector:
                subsectors.add(dto.industry_subsector)
            if dto.industry_segment:
                segments.add(dto.industry_segment)
            if dto.market:
                markets.add(dto.market)

        facets = {
            "industry_sector": sorted(sectors),
            "industry_subsector": sorted(subsectors),
            "industry_segment": sorted(segments),
            "market": sorted(markets),
        }

        if self._logger is not None:
            self._logger.log(
                "GetCompanyFacetsUseCase returned facets with sizes "
                f"{ {k: len(v) for k, v in facets.items()} }",
                level="debug",
            )

        return CompanyFacetsResult(facets=facets)
