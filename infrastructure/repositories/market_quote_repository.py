# infrastructure/repositories/market_quote_repository.py
from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.orm import Session

from domain.dtos.market_quote_dto import MarketQuoteDTO
from infrastructure.models.market_quote_model import MarketQuoteModel


class MarketQuoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def bulk_upsert(self, quotes: Sequence[MarketQuoteDTO]) -> None:
        if not quotes:
            return
        stmt = sqlite_upsert(MarketQuoteModel).values(
            [
                dict(
                    provider=q.provider,
                    symbol=q.symbol,
                    day=q.day,
                    close=q.close,
                    adj_close=q.adjusted_close,
                    currency=q.currency,
                )
                for q in quotes
            ]
        ).on_conflict_do_update(
            index_elements=[
                MarketQuoteModel.provider,
                MarketQuoteModel.symbol,
                MarketQuoteModel.day,
            ],
            set_={
                "close": getattr(sqlite_upsert(MarketQuoteModel).excluded, "close"),
                "adj_close": getattr(sqlite_upsert(MarketQuoteModel).excluded, "adj_close"),
                "currency": getattr(sqlite_upsert(MarketQuoteModel).excluded, "currency"),
            },
        )
        self.session.execute(stmt)

    def get_between(self, symbol: str, start: date, end: date) -> Sequence[MarketQuoteDTO]:
        rows = (
            self.session.execute(
                select(MarketQuoteModel)
                .where(
                    MarketQuoteModel.symbol == symbol,
                    MarketQuoteModel.day >= start,
                    MarketQuoteModel.day <= end,
                )
                .order_by(MarketQuoteModel.day.asc())
            )
            .scalars()
            .all()
        )
        return [
            MarketQuoteDTO(
                r.provider, r.symbol, r.day, r.close, r.adj_close, r.currency
            )
            for r in rows
        ]

    def latest_on_or_before(self, symbol: str, day: date) -> Optional[MarketQuoteDTO]:
        row = (
            self.session.execute(
                select(MarketQuoteModel)
                .where(
                    MarketQuoteModel.symbol == symbol,
                    MarketQuoteModel.day <= day,
                )
                .order_by(MarketQuoteModel.day.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if not row:
            return None
        return MarketQuoteDTO(
            row.provider,
            row.symbol,
            row.day,
            row.close,
            row.adj_close,
            row.currency,
        )
