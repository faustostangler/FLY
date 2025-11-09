from __future__ import annotations

from dataclasses import dataclass
from typing import List

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort
from domain.value_objects.company_filters import CompanyFilterQuery

DEFAULT_LIMIT = 200


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


class SearchCompaniesUseCase:
    def __init__(
        self,
        *,
        repository: RepositoryCompanyEligiblePort,
        uow_factory: UowFactoryPort,
        logger: LoggerPort | None = None,
    ) -> None:
        self._repository = repository
        self._uow_factory = uow_factory
        self._logger = logger

    def __call__(
        self,
        query: CompanyFilterQuery | None = None,
        *,
        limit: int | None = None,
    ) -> CompanySearchResult:
        query = query or CompanyFilterQuery()
        return self.run(query=query, limit=limit)

    def run(
        self,
        *,
        query: CompanyFilterQuery,
        limit: int | None = None,
    ) -> CompanySearchResult:
        effective_limit = limit or DEFAULT_LIMIT

        with self._uow_factory() as uow:
            dtos: List[CompanyEligibleDTO] = self._repository.search(
                query=query,
                uow=uow,
                limit=effective_limit,
            )

        items = [self._to_item(dto) for dto in dtos]

        if self._logger is not None:
            self._logger.log(
                f"SearchCompaniesUseCase returned {len(items)} items "
                f"(limit={effective_limit})",
                level="debug",
            )

        return CompanySearchResult(
            items=items,
            total=len(items),
        )

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
