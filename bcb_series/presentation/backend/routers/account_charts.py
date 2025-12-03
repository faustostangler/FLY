from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.usecases.get_account_series import GetAccountSeriesUseCase
from presentation.backend.dependencies.account_chart_dependencies import (
    get_account_series_usecase,
)
from presentation.backend.dto.chart_dto import ChartDTO, PlotlyTraceDTO

router = APIRouter(
    prefix="/api/charts/accounts",
    tags=["charts"],
)


@router.get("/line/{ticker}", response_model=ChartDTO)
async def get_account_line_chart(
    ticker: str,
    account_code: str = Query(..., description="Código da conta, ex: 02.03"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    usecase: GetAccountSeriesUseCase = Depends(get_account_series_usecase),
) -> ChartDTO:
    series = usecase(
        ticker=ticker,
        account_code=account_code,
        start_date=start_date,
        end_date=end_date,
    )

    if not series.points:
        # print(series)

        layout = {
            "title": f"{series.label} – {series.ticker}",
            "xaxis": {"title": "Data"},
            "yaxis": {"title": "Valor"},
        }
        return ChartDTO(data=[], layout=layout)

    trace = PlotlyTraceDTO(
        x=[point.date for point in series.points],
        y=[point.value for point in series.points],
        type="scatter",
        mode="lines",
        name=f"{series.account_code} – {series.label}",
        extra={
            "hovertemplate": "%{x}<br>Valor: %{y}<extra></extra>",
        },
    )

    layout = {
        "title": f"{series.label} – {series.ticker}",
        "xaxis": {"title": "Data"},
        "yaxis": {"title": "Valor"},
    }

    return ChartDTO(data=[trace], layout=layout)
