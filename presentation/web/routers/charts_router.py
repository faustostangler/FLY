from fastapi import APIRouter, Depends, Query

from presentation.web.dto.chart_dto import ChartDTO
from presentation.web.mappers.stock_quote_chart_mapper import (
    stock_quotes_to_price_chart,
)
from presentation.web.dependencies.stock_quote_dependencies import (
    get_stock_quote_history_usecase,
)
from application.usecases.get_stock_quote_history import GetStockQuoteHistoryUseCase

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/{ticker}", response_model=ChartDTO)
async def get_stock_chart(
    ticker: str,
    limit: int = Query(365, ge=1, le=2000),
    usecase: GetStockQuoteHistoryUseCase = Depends(get_stock_quote_history_usecase),
) -> ChartDTO:
    quotes = usecase(ticker=ticker, limit=limit)
    return stock_quotes_to_price_chart(quotes)
