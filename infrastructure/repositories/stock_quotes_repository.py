# infrastructure/repositories/stock_quotes_repository.py
from __future__ import annotations

from typing import Iterable, List

from sqlalchemy import insert

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.stock_value import QuotesWriterPort
from domain.entities.stock_value import Quote
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.models.stock_quote_model import StockQuoteModel


class SqlAlchemyQuotesRepository(EngineSetup, QuotesWriterPort):
    """Repository responsible for persisting normalized quotes."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        super().__init__(config.database.connection_string, logger)

    def upsert_quotes(self, quotes: Iterable[Quote]) -> None:
        buffered: List[Quote] = [quote for quote in quotes if quote is not None]
        if not buffered:
            return

        with self.Session() as session:
            for quote in buffered:
                stmt = (
                    insert(StockQuoteModel)
                    .values(
                        ticker=quote.ticker.code,
                        date=quote.date,
                        close_adj=float(quote.close_adj),
                    )
                    .prefix_with("OR REPLACE")
                )
                session.execute(stmt)
            session.commit()
