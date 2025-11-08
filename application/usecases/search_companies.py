from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.value_objects.company_filters import CompanyFilterQuery, CompanyField


@dataclass(frozen=True)
class CompanySearchResultItem:
    company_name: str
    trading_name: str | None
    tickers: list[str]
    sector: str | None
    subsector: str | None
    segment: str | None
    market: str | None
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
        filters = self._extract_simple_filters(query)

        with self._uow_factory() as uow:
            dtos: list[CompanyEligibleDTO] = self._repository.list(
                uow=uow,
                cvm_code=filters.get("cvm_code"),
                company_name=filters.get("company_name"),
                segment=filters.get("segment"),
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

    def _extract_simple_filters(self, query: CompanyFilterQuery) -> dict[str, str]:
        filters: dict[str, str] = {}

        for clause in query.clauses:
            condition = clause.condition
            if condition is None or not condition.values:
                continue
            value = condition.values[0]
            if not value:
                continue
            if condition.field == CompanyField.COMPANY_NAME:
                filters.setdefault("company_name", value)
            elif condition.field == CompanyField.SEGMENT:
                filters.setdefault("segment", value)
            elif condition.field == CompanyField.CVM_CODE:
                filters.setdefault("cvm_code", value)

        return filters

    def _to_item(self, dto: CompanyEligibleDTO) -> CompanySearchResultItem:
        tickers = [ticker for ticker in (dto.ticker_codes or ()) if ticker]

        return CompanySearchResultItem(
            company_name=dto.company_name or "",
            trading_name=dto.trading_name,
            tickers=tickers,
            sector=getattr(dto, "industry_sector", None)
            or getattr(dto, "company_sector", None),
            subsector=getattr(dto, "industry_subsector", None)
            or getattr(dto, "company_subsector", None),
            segment=getattr(dto, "industry_segment", None)
            or getattr(dto, "company_segment", None),
            market=dto.market,
            institution_common=dto.institution_common,
            institution_preferred=dto.institution_preferred,
        )

    def _build_facets(
        self,
        items: list[CompanySearchResultItem],
    ) -> Dict[str, List[str]]:
        facets: Dict[str, set[str]] = {
            "sector": set(),
            "subsector": set(),
            "segment": set(),
            "market": set(),
        }

        for item in items:
            if item.sector:
                facets["sector"].add(item.sector)
            if item.subsector:
                facets["subsector"].add(item.subsector)
            if item.segment:
                facets["segment"].add(item.segment)
            if item.market:
                facets["market"].add(item.market)

        return {key: sorted(values) for key, values in facets.items()}
