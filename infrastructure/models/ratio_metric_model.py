from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.ratio_result_dto import RatioResultDTO
from infrastructure.models.base_model import BaseModel, _YMDDate


class RatioMetricModel(BaseModel):
    __tablename__ = "tbl_ratio_metric"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_company.company_name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    ratio_code: Mapped[str] = mapped_column(String(64), nullable=False)
    date: Mapped[datetime] = mapped_column(_YMDDate(), nullable=False, index=True)
    value: Mapped[float | None] = mapped_column(Float)
    version: Mapped[str] = mapped_column(String(128), nullable=False)
    calculation_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    input_versions: Mapped[str] = mapped_column(Text, nullable=False)
    input_hashes: Mapped[str] = mapped_column(Text, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint(
            "company_name", "ratio_code", "date", "version", name="uq_ratio_metric_versioned"
        ),
        Index("ix_ratio_metric_current", "company_name", "ratio_code", "date", "is_current"),
    )

    @staticmethod
    def _serialize_pairs(pairs: tuple[tuple[str, str | None], ...]) -> str:
        return json.dumps([[k, v] for k, v in pairs])

    @staticmethod
    def _deserialize_pairs(data: str) -> tuple[tuple[str, str | None], ...]:
        loaded = json.loads(data or "[]")
        return tuple((str(k), v if v is None else str(v)) for k, v in loaded)

    @classmethod
    def from_dto(cls, dto: RatioResultDTO) -> "RatioMetricModel":
        return cls(
            id=dto.id,
            company_name=dto.company_id,
            ratio_code=dto.ratio_code,
            date=dto.date,
            value=dto.value,
            version=dto.version,
            calculation_hash=dto.calculation_hash,
            input_versions=cls._serialize_pairs(dto.input_versions),
            input_hashes=cls._serialize_pairs(dto.input_hashes),
            is_current=dto.is_current,
        )

    def to_dto(self) -> RatioResultDTO:
        return RatioResultDTO(
            id=self.id,
            company_id=self.company_name,
            ratio_code=self.ratio_code,
            date=self.date,
            value=self.value,
            version=self.version,
            calculation_hash=self.calculation_hash,
            input_versions=self._deserialize_pairs(self.input_versions),
            input_hashes=self._deserialize_pairs(self.input_hashes),
            is_current=self.is_current,
        )
