from __future__ import annotations

from typing import List

from application.dtos.company_accounts_series_dto import CompanyAccountsSeriesDTO
from presentation.backend.dto.chart_dto import ChartDTO, PlotlyTraceDTO


def company_accounts_to_chart(dto: CompanyAccountsSeriesDTO) -> ChartDTO:
    traces: List[PlotlyTraceDTO] = []

    for series in dto.series:
        x = [point.date for point in series.points]
        y = [point.value for point in series.points]
        traces.append(
            PlotlyTraceDTO(
                x=x,
                y=y,
                type="scatter",
                mode="lines",
                name=f"{series.account_code} - {series.label}",
                extra={"ticker": series.ticker},
            )
        )

    layout = {
        "title": f"Ratios – {dto.company_name}",
        "xaxis": {"title": "Data"},
        "yaxis": {"title": "Valor"},
    }

    meta = dict(dto.meta)
    if dto.cache_info:
        meta.setdefault("cache", {})
        meta["cache"].update(
            {
                "key": dto.cache_info.cache_key,
                "hit": dto.cache_info.hit,
            }
        )

    return ChartDTO(
        data=traces,
        layout=layout,
        meta=meta,
    )


__all__ = ["company_accounts_to_chart"]

