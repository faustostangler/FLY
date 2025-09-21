from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base_model import BaseModel


class StockQuoteModel(BaseModel):
    """SQLAlchemy ORM model storing normalized stock quotes (OHLC + Adj Close)."""

    __tablename__ = "tbl_stock_quote"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)

    # Adj Close normalizado (fallback para Close quando necessário no adapter)
    close_adj: Mapped[float] = mapped_column(Float, nullable=False)

    # Volume negociado
    volume: Mapped[int] = mapped_column(nullable=False)
