from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from application.usecases.get_company_accounts_chart import GetCompanyAccountsChartUseCase
from domain.exceptions import DomainError
from domain.value_objects import SearchFilterTree
from presentation.backend.dependencies.ratios_chart_dependencies import (
    get_company_accounts_chart_usecase,
)
from presentation.backend.dependencies.auth import get_current_user
from presentation.backend.dto.chart_dto import ChartDTO
from presentation.backend.dto.company_accounts_chart_request_dto import (
    CompanyAccountsChartRequestDTO,
)
from presentation.backend.mappers.accounts_series_chart_mapper import (
    company_accounts_to_chart,
)

router = APIRouter(prefix="/api/charts/ratios", tags=["charts-ratios"])


def _to_filter_tree(dto) -> SearchFilterTree | None:
    if dto is None:
        return None
    return dto.to_domain()


@router.post("/company", response_model=ChartDTO)
async def get_company_ratios_chart(
    payload: CompanyAccountsChartRequestDTO,
    _current_user: dict = Depends(get_current_user),
    usecase: GetCompanyAccountsChartUseCase = Depends(
        get_company_accounts_chart_usecase
    ),
) -> ChartDTO:
    filter_tree = _to_filter_tree(payload.filters)
    try:
        series_dto = usecase(
            company_name=payload.company_name,
            accounts=payload.accounts,
            filters=filter_tree,
        )
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return company_accounts_to_chart(series_dto)
