from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.ratio_dto import RatioDTO
from infrastructure.models.base_model import BaseModel, _YMDDate


class RatioModel(BaseModel):
    """SQLAlchemy model that stores financial ratios in long (tidy) format."""

    __tablename__ = "tbl_ratios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cnpj_root: Mapped[str | None] = mapped_column(String(16))
    date: Mapped[datetime] = mapped_column(_YMDDate(), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(8), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(32))
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(16))
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "date",
            "scope",
            "ticker",
            "metric_code",
            "version",
            name="uq_ratios_natural_key",
        ),
        Index("ix_ratios_company_metric_date", "company_id", "metric_code", "date"),
    )

    @staticmethod
    def from_dto(dto: RatioDTO) -> "RatioModel":
        return RatioModel(
            id=dto.id,
            company_id=dto.company_id,
            cnpj_root=dto.cnpj_root,
            date=dto.date,
            scope=dto.scope,
            ticker=dto.ticker,
            metric_code=dto.metric_code,
            metric_name=dto.metric_name,
            value=dto.value,
            unit=dto.unit,
            version=dto.version,
            is_current=dto.is_current,
            hash=dto.hash,
            created_at=dto.created_at,
        )

    def to_dto(self) -> RatioDTO:
        return RatioDTO(
            id=self.id,
            company_id=self.company_id,
            cnpj_root=self.cnpj_root,
            date=self.date,
            scope=self.scope,
            ticker=self.ticker,
            metric_code=self.metric_code,
            metric_name=self.metric_name,
            value=self.value,
            unit=self.unit,
            version=self.version,
            is_current=self.is_current,
            hash=self.hash,
            created_at=self.created_at,
        )
