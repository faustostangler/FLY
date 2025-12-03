from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from application.usecases.get_company_accounts_chart import (
    GetCompanyAccountsChartUseCase,
)
from domain import DomainError
from domain.value_objects import SearchFilterTree
from presentation.backend.dependencies.ratios_chart_dependencies import (
    get_company_accounts_chart_usecase,
)
from presentation.backend.dto.chart_dto import ChartDTO
from presentation.backend.dto.company_accounts_chart_request_dto import (
    CompanyAccountsChartRequestDTO,
)
from presentation.backend.dto.search_filters_dto import SearchFiltersDTO
from presentation.backend.mappers.accounts_series_chart_mapper import (
    company_accounts_to_chart,
)


router = APIRouter(prefix="/api/charts/ratios", tags=["charts-ratios"])


@router.post("/company", response_model=ChartDTO)
async def get_company_ratios_chart(
    payload: CompanyAccountsChartRequestDTO,
    usecase: GetCompanyAccountsChartUseCase = Depends(
        get_company_accounts_chart_usecase
    ),
) -> ChartDTO:
    filter_tree = _map_filters(payload.filters)

    try:
        series_dto = usecase(
            company_name=payload.company_name,
            accounts=payload.accounts,
            filters=filter_tree,
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not series_dto.series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma série encontrada para os parâmetros informados.",
        )

    return company_accounts_to_chart(series_dto)


def _map_filters(filters: SearchFiltersDTO | None) -> SearchFilterTree | None:
    if filters is None:
        return None
    return filters.to_domain()


__all__ = ["router"]

