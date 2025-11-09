from __future__ import annotations

from dataclasses import dataclass
from typing import List

from application.dtos.company_facets_dto import CompanyFacetsResponseDTO
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort

from application.services.company_facets_builder import build_company_facets

DEFAULT_FACETS_BATCH_SIZE = 1000000


@dataclass
class GetCompanyFacetsUseCase:
    repository: RepositoryCompanyEligiblePort
    uow_factory: UowFactoryPort

    def __call__(self) -> CompanyFacetsResponseDTO:
        with self.uow_factory() as uow:
            items: List[CompanyEligibleDTO] = self.repository.get_all(
                uow=uow,
                batch_size=DEFAULT_FACETS_BATCH_SIZE,
            )

        facets = build_company_facets(items)
        return CompanyFacetsResponseDTO(facets=facets)
