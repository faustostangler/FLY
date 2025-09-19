# infrastructure/models/market_quote_model.py
from __future__ import annotations

from datetime import date

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base_model import BaseModel


class MarketQuoteModel(BaseModel):
    __tablename__ = "tbl_market_quotes"

    provider: Mapped[str] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)  # TEXT 'YYYY-MM-DD'
    close: Mapped[float]
    adj_close: Mapped[float]
    currency: Mapped[str]


Index("ix_market_symbol_day", MarketQuoteModel.symbol, MarketQuoteModel.day)
