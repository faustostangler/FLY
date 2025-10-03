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

from domain.dtos.indicators_dto import IndicatorRecordDTO
from infrastructure.models.base_model import (
    BaseModel,
    _YMDDate,
)


class IndicatorModel(BaseModel):
    __tablename__ = "tbl_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source: Mapped[str] = mapped_column(String(), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(), index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(_YMDDate(), index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("source", "code", "date", name="uq_indicator_source_name_date"),
        Index("ix_indicator_source_name", "source", "name"),
    )

    @staticmethod
    def from_dto(dto: IndicatorRecordDTO) -> "IndicatorModel":
        return IndicatorModel(
            id=dto.id,
            source=dto.source,
            name=dto.name,
            code=dto.code,
            date=dto.date,
            value=dto.value,
        )

    def to_dto(self) -> IndicatorRecordDTO:
        return IndicatorRecordDTO(
            id=self.id,
            source=self.source,
            name=self.name,
            code=self.code,
            date=self.date,
            value=self.value,
        )
