# infrastructure/models/stock_quote_model.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.value_objects.indicators import Coverage, Frequency, Period
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
    frequency: Mapped[str] = mapped_column(String(), nullable=False)
    coverage: Mapped[str] = mapped_column(String(), nullable=False)
    observation_start: Mapped[datetime] = mapped_column(_YMDDate(), nullable=False)
    observation_end: Mapped[datetime] = mapped_column(_YMDDate(), nullable=False)
    observation_date: Mapped[datetime] = mapped_column(_YMDDate(), index=True, nullable=False)
    availability_date: Mapped[datetime] = mapped_column(_YMDDate(), index=True, nullable=False)
    value: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint(
            "source", "code", "observation_date", name="uq_indicator_source_name_date"
        ),
        Index("ix_indicator_source_name", "source", "name"),
    )

    @staticmethod
    def from_dto(dto: IndicatorRecordDTO) -> "IndicatorModel":
        return IndicatorModel(
            id=dto.id,
            source=dto.source,
            name=dto.name,
            code=dto.code,
            frequency=dto.frequency.value,
            coverage=dto.coverage.value,
            observation_start=dto.observation_start,
            observation_end=dto.observation_end,
            observation_date=dto.observation_date,
            availability_date=dto.availability_date,
            value=dto.value,
        )

    def to_dto(self) -> IndicatorRecordDTO:
        return IndicatorRecordDTO(
            id=self.id,
            source=self.source,
            name=self.name,
            code=self.code,
            frequency=Frequency.from_string(self.frequency),
            coverage=Coverage.from_string(self.coverage),
            observation_period=Period(self.observation_start, self.observation_end),
            observation_date=self.observation_date,
            availability_date=self.availability_date,
            value=self.value,
        )
