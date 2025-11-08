from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.value_objects.company_filters import CompanyFilterQuery


@dataclass(frozen=True)
class CompanySearchResultItem:
    company_name: str
    trading_name: str | None
    tickers: list[str]
    market: str | None
    industry_sector: str | None
    industry_subsector: str | None
    industry_segment: str | None
    institution_common: str | None
    institution_preferred: str | None


@dataclass(frozen=True)
class CompanySearchResult:
    items: list[CompanySearchResultItem]
    total: int
    facets: Dict[str, List[str]]


class SearchCompaniesUseCase:
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

    def __call__(
        self,
        query: CompanyFilterQuery | None = None,
    ) -> CompanySearchResult:
        query = query or CompanyFilterQuery()
        return self.run(query=query)

    def run(self, *, query: CompanyFilterQuery) -> CompanySearchResult:
        with self._uow_factory() as uow:
            dtos: list[CompanyEligibleDTO] = self._repository.search(
                uow=uow,
                query=query,
            )

        items = [self._to_item(dto) for dto in dtos]
        facets = self._build_facets(items)

        if self._logger is not None:
            self._logger.log(
                f"SearchCompaniesUseCase returned {len(items)} items",
                level="debug",
            )

        return CompanySearchResult(
            items=items,
            total=len(items),
            facets=facets,
        )

    def _to_item(self, dto: CompanyEligibleDTO) -> CompanySearchResultItem:
        tickers = [ticker for ticker in (dto.ticker_codes or ()) if ticker]

        return CompanySearchResultItem(
            company_name=dto.company_name or "",
            trading_name=dto.trading_name,
            tickers=tickers,
            market=dto.market,
            industry_sector=dto.industry_sector
            or getattr(dto, "company_sector", None),
            industry_subsector=dto.industry_subsector
            or getattr(dto, "company_subsector", None),
            industry_segment=dto.industry_segment
            or getattr(dto, "company_segment", None),
            institution_common=dto.institution_common,
            institution_preferred=dto.institution_preferred,
        )

    def _build_facets(
        self,
        items: list[CompanySearchResultItem],
    ) -> Dict[str, List[str]]:
        facets: Dict[str, set[str]] = {
            "industry_sector": set(),
            "industry_subsector": set(),
            "industry_segment": set(),
            "market": set(),
        }

        for item in items:
            if item.industry_sector:
                facets["industry_sector"].add(item.industry_sector)
            if item.industry_subsector:
                facets["industry_subsector"].add(item.industry_subsector)
            if item.industry_segment:
                facets["industry_segment"].add(item.industry_segment)
            if item.market:
                facets["market"].add(item.market)

        return {key: sorted(values) for key, values in facets.items()}
