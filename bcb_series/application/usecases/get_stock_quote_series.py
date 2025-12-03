# application/usecases/get_stock_quote_series.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from application.ports.uow_port import UowFactoryPort
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort


@dataclass
class GetStockQuoteSeriesUseCase:
    """
    Caso de uso de aplicação.

    Entrada: ticker (str)
    Saída: lista de StockQuoteDTO ordenados por data.
    Não conhece Plotly, JSON, FastAPI, nada de apresentação.
    Apenas orquestra repositório + UoW.
    """
    repository: RepositoryStockQuotePort
    uow_factory: UowFactoryPort

    def __call__(self, *, ticker: str) -> List[StockQuoteDTO]:
        """
        Retorna toda a série histórica para o ticker informado.
        """
        with self.uow_factory() as uow:
            quotes: List[StockQuoteDTO] = self.repository.get_by_column_values(
                values={"ticker": ticker},
                uow=uow,
            )

        # garantia de ordenação por data na borda da aplicação
        quotes.sort(key=lambda q: q.date)
        return quotes
