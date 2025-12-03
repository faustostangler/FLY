# infrastructure/models/stock_quote_model.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.stock_quote_dto import StockQuoteDTO
from infrastructure.models.base_model import (
    BaseModel,
    _YMDDate,
)


class StockQuoteModel(BaseModel):
    __tablename__ = "tbl_stock_quote"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_name: Mapped[str] = mapped_column(
        String, ForeignKey("tbl_company.company_name", ondelete="RESTRICT"), index=True, nullable=False
    )

    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    date: Mapped[datetime] = mapped_column(_YMDDate(), index=True, nullable=False)

    open: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    adj_close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_stock_quote_ticker_date"),
        Index("ix_stock_quote_company_date", "company_name", "date"),
    )

    @staticmethod
    def from_dto(dto: StockQuoteDTO) -> "StockQuoteModel":
        return StockQuoteModel(
            id=dto.id,
            company_name=dto.company_name,
            ticker=dto.ticker,
            date=dto.date,
            open=dto.open,
            low=dto.low,
            high=dto.high,
            close=dto.close,
            adj_close=dto.adj_close,
            volume=dto.volume,
            currency=dto.currency,
        )

    def to_dto(self) -> StockQuoteDTO:
        return StockQuoteDTO(
            id=self.id,
            company_name=self.company_name,
            ticker=self.ticker,
            date=self.date,
            open=self.open,
            low=self.low,
            high=self.high,
            close=self.close,
            adj_close=self.adj_close,
            volume=self.volume,
            currency=self.currency,
        )
