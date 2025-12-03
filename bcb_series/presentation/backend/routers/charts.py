# presentation/backend/routers/charts.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from application.usecases.get_stock_quote_series import GetStockQuoteSeriesUseCase
from presentation.backend.dependencies.stock_quote_dependencies import get_stock_quote_usecase
from presentation.backend.dto.chart_dto import ChartDTO, PlotlyTraceDTO

router = APIRouter(
    prefix="/charts",
    tags=["charts"],
)


@router.get("/{ticker}", response_model=ChartDTO)
async def get_chart_for_ticker(
    ticker: str,
    usecase: GetStockQuoteSeriesUseCase = Depends(get_stock_quote_usecase),
) -> ChartDTO:
    """
    Endpoint fino (camada de apresentação).

    1. Recebe o ticker
    2. Chama o caso de uso (aplicação)
    3. Converte StockQuoteDTO -> ChartDTO genérico para Plotly
    """
    quotes = usecase(ticker=ticker)

    if not quotes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum dado encontrado para ticker '{ticker}'",
        )

    # Monta arrays para o Plotly (x = datas, y = closes)
    x = [q.date for q in quotes]
    y = [q.close for q in quotes]

    trace = PlotlyTraceDTO(
        x=x,
        y=y,
        type="scatter",
        mode="lines",
        name=ticker,
        extra={"hovertemplate": "%{x}<br>Close: %{y}<extra></extra>"},
    )

    layout = {
        "title": f"Preço de fechamento – {ticker}",
        "xaxis": {"title": "Data"},
        "yaxis": {"title": "Preço de fechamento"},
    }

    return ChartDTO(
        data=[trace],
        layout=layout,
    )
