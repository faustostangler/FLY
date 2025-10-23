from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.quarter_price_dto import QuarterPriceDTO
from infrastructure.models.base_model import BaseModel, _YMDDate


class QuarterPriceModel(BaseModel):
    __tablename__ = "tbl_quarter_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("tbl_company.company_name", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quarter: Mapped[object] = mapped_column(_YMDDate(), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    asof: Mapped[object] = mapped_column(_YMDDate(), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("company_name", "quarter", "method", name="uq_quarter_price_identity"),
    )

    @staticmethod
    def from_dto(dto: QuarterPriceDTO) -> "QuarterPriceModel":
        return QuarterPriceModel(
            id=dto.id,
            company_name=dto.company_name,
            quarter=dto.quarter,
            method=dto.method,
            price=dto.price,
            asof=dto.asof,
            currency=dto.currency,
            version=dto.version or 1,
        )

    def to_dto(self) -> QuarterPriceDTO:
        return QuarterPriceDTO(
            id=self.id,
            company_name=self.company_name,
            quarter=self.quarter,
            method=self.method,
            price=self.price,
            asof=self.asof,
            currency=self.currency,
            version=self.version,
        )
