from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from application.dtos.company_search_dto import (
    CompanySearchResponseDTO,
    CompanySearchResultDTO,
)
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort
from domain.value_objects.company_filters import CompanyFilterQuery, CompanyField


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
        with self.uow_factory() as uow:
            dtos: List[CompanyEligibleDTO] = self.repository.search(
                query,
                uow=uow,
                limit=limit or DEFAULT_LIMIT,
            )

        items = [self._to_result(dto) for dto in dtos]
        facets = self._build_facets(dtos)
        return CompanySearchResponseDTO(items=items, total=len(items), facets=facets)

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

    def _build_facets(
        self,
        items: Iterable[CompanyEligibleDTO],
    ) -> Dict[str, List[str]]:
        string_fields = [
            CompanyField.ISSUING_COMPANY,
            CompanyField.TRADING_NAME,
            CompanyField.COMPANY_NAME,
            CompanyField.CNPJ,
            CompanyField.MARKET,
            CompanyField.INDUSTRY_SECTOR,
            CompanyField.INDUSTRY_SUBSECTOR,
            CompanyField.INDUSTRY_SEGMENT,
            CompanyField.INDUSTRY_CLASSIFICATION,
            CompanyField.INDUSTRY_CLASSIFICATION_ENG,
            CompanyField.ACTIVITY,
            CompanyField.COMPANY_SEGMENT,
            CompanyField.COMPANY_SEGMENT_ENG,
            CompanyField.COMPANY_CATEGORY,
            CompanyField.COMPANY_TYPE,
            CompanyField.LISTING_SEGMENT,
            CompanyField.REGISTRAR,
            CompanyField.WEBSITE,
            CompanyField.INSTITUTION_COMMON,
            CompanyField.INSTITUTION_PREFERRED,
            CompanyField.STATUS,
            CompanyField.MARKET_INDICATOR,
            CompanyField.CODE,
            CompanyField.TYPE_BDR,
            CompanyField.REASON,
        ]

        boolean_fields = [
            CompanyField.HAS_BDR,
            CompanyField.HAS_QUOTATION,
            CompanyField.HAS_EMISSIONS,
        ]

        buckets: Dict[str, set[str]] = {
            field.value: set() for field in string_fields + boolean_fields
        }

        for item in items:
            for field in string_fields:
                value = getattr(item, field.value, None)
                if value:
                    buckets[field.value].add(value)

            for field in boolean_fields:
                value = getattr(item, field.value, None)
                if value is None:
                    continue
                buckets[field.value].add("true" if value else "false")

        return {
            key: sorted({v for v in values if v})
            for key, values in buckets.items()
            if values
        }
