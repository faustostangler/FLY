from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from application.dtos.company_search_dto import (
    CompanySearchResponseDTO,
    CompanySearchResultDTO,
)
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.value_objects.company_filters import CompanyFilterQuery, CompanyField


DEFAULT_LIMIT = 200


@dataclass
class SearchCompaniesUseCase:
    repository: RepositoryCompanyDataPort
    uow_factory: UowFactoryPort

    def __call__(
        self,
        query: CompanyFilterQuery | None = None,
        *,
        limit: int | None = None,
    ) -> CompanySearchResponseDTO:
        query = query or CompanyFilterQuery()
        with self.uow_factory() as uow:
            dtos: List[CompanyDataDTO] = self.repository.search(
                query,
                uow=uow,
                limit=limit or DEFAULT_LIMIT,
            )

        items = [self._to_result(dto) for dto in dtos]
        facets = self._build_facets(items)
        return CompanySearchResponseDTO(items=items, total=len(items), facets=facets)

    def _to_result(self, dto: CompanyDataDTO) -> CompanySearchResultDTO:
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

    def _build_facets(
        self,
        items: Iterable[CompanySearchResultDTO],
    ) -> Dict[str, List[str]]:
        buckets: Dict[str, set[str]] = {
            CompanyField.SECTOR.value: set(),
            CompanyField.SUBSECTOR.value: set(),
            CompanyField.SEGMENT.value: set(),
            CompanyField.COMPANY_NAME.value: set(),
            CompanyField.TRADING_NAME.value: set(),
            CompanyField.TICKER.value: set(),
            CompanyField.INSTITUTION_COMMON.value: set(),
            CompanyField.INSTITUTION_PREFERRED.value: set(),
            CompanyField.MARKET.value: set(),
        }

        for item in items:
            if item.company_name:
                buckets[CompanyField.COMPANY_NAME.value].add(item.company_name)
            if item.trading_name:
                buckets[CompanyField.TRADING_NAME.value].add(item.trading_name)
            for ticker in item.tickers:
                if ticker:
                    buckets[CompanyField.TICKER.value].add(ticker)
            if item.sector:
                buckets[CompanyField.SECTOR.value].add(item.sector)
            if item.subsector:
                buckets[CompanyField.SUBSECTOR.value].add(item.subsector)
            if item.segment:
                buckets[CompanyField.SEGMENT.value].add(item.segment)
            if item.market:
                buckets[CompanyField.MARKET.value].add(item.market)
            if item.institution_common:
                buckets[CompanyField.INSTITUTION_COMMON.value].add(item.institution_common)
            if item.institution_preferred:
                buckets[CompanyField.INSTITUTION_PREFERRED.value].add(
                    item.institution_preferred
                )

        return {
            key: sorted({v for v in values if v})
            for key, values in buckets.items()
            if values
        }
