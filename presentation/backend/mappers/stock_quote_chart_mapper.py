from typing import List

from domain.dtos.stock_quote_dto import StockQuoteDTO
from presentation.backend.dto.chart_dto import ChartDTO


def stock_quotes_to_price_chart(quotes: List[StockQuoteDTO]) -> ChartDTO:
    if not quotes:
        return ChartDTO(
            title="Sem dados",
            layout={"xaxis": {"title": "Data"}, "yaxis": {"title": "Fechamento"}},
            data=[],
        )

    quotes_sorted = sorted(quotes, key=lambda q: q.date)

    x = [q.date.isoformat() for q in quotes_sorted]
    y = [q.close for q in quotes_sorted]
    ticker = quotes_sorted[0].ticker

    return ChartDTO(
        title=f"Histórico de {ticker}",
        layout={
            "xaxis": {"title": "Data"},
            "yaxis": {"title": "Preço de fechamento"},
        },
        data=[
            {
                "x": x,
                "y": y,
                "type": "scatter",
                "mode": "lines",
                "name": ticker,
            }
        ],
    )
