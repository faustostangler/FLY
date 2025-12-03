from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.models.base_model import BaseModel, _YMDDate


class FinancialStatementModel(BaseModel):
    """Modelo ORM simplificado para séries temporais de contas."""

    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    account_code: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    reference_date: Mapped[datetime] = mapped_column(
        _YMDDate(), index=True, nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "account_code",
            "reference_date",
            name="uq_financial_statement",
        ),
    )
