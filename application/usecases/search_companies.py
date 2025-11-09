from __future__ import annotations

from dataclasses import dataclass
from typing import List

from application.dtos.company_search_dto import CompanySearchResponseDTO
from application.dtos.company_search_result_dto import CompanySearchResultDTO
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort
from domain.value_objects.company_filters import CompanyFilterQuery

from application.services.company_facets_builder import build_company_facets


DEFAULT_LIMIT = 200


@dataclass
class SearchCompaniesUseCase:
    repository: RepositoryCompanyEligiblePort
    uow_factory: UowFactoryPort

    def __call__(
        self,
        query: CompanyFilterQuery | None = None,
        *,
        limit: int | None = None,
    ) -> CompanySearchResponseDTO:
        query = query or CompanyFilterQuery()
        effective_limit = limit or DEFAULT_LIMIT

        with self.uow_factory() as uow:
            dtos: List[CompanyEligibleDTO] = self.repository.search(
                query,
                uow=uow,
                limit=effective_limit,
            )

        items = [self._to_result(dto) for dto in dtos]
        facets = build_company_facets(dtos)

        total = len(items)

        return CompanySearchResponseDTO(
            items=items,
            total=total,
            facets=facets,
        )

    def _to_result(self, dto: CompanyEligibleDTO) -> CompanySearchResultDTO:
        return CompanySearchResultDTO(
            company_name=dto.company_name or "",
            trading_name=dto.trading_name,
            tickers=list(dto.ticker_codes or []),
            sector=dto.industry_sector,
            subsector=dto.industry_subsector,
            segment=dto.industry_segment,
            market=dto.market,
            institution_common=dto.institution_common,
            institution_preferred=dto.institution_preferred,
        )

